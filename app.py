"""Small, single-site order system for wholesale egg sales."""

from __future__ import annotations

import hashlib
import hmac
import io
import json
import os
import secrets
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from zoneinfo import ZoneInfo

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


ROOT = Path(__file__).resolve().parent
DB_PATH = Path(os.getenv("COMERCIALIZADORA_DB", ROOT / "data" / "app.sqlite3"))
COOKIE_SECURE = os.getenv("COMERCIALIZADORA_SECURE_COOKIE", "0") == "1"
BUSINESS_TZ = ZoneInfo("America/Lima")
app = FastAPI(title="Comercializadora Viviana", docs_url=None, redoc_url=None)


@contextmanager
def database():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH, timeout=15)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    con.execute("PRAGMA journal_mode = WAL")
    try:
        yield con
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()


def init_db():
    with database() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY, username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL, salt TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS sessions (
            token_hash TEXT PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id),
            expires_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY, name TEXT NOT NULL, document TEXT NOT NULL DEFAULT '',
            phone TEXT NOT NULL DEFAULT '', address TEXT NOT NULL DEFAULT '',
            district TEXT NOT NULL DEFAULT '', notes TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE, category TEXT NOT NULL,
            unit TEXT NOT NULL, sold_by_weight INTEGER NOT NULL DEFAULT 1,
            price_cents INTEGER NOT NULL DEFAULT 0, active INTEGER NOT NULL DEFAULT 1
        );
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY, code TEXT UNIQUE, client_id INTEGER NOT NULL REFERENCES clients(id),
            product_id INTEGER NOT NULL REFERENCES products(id), created_by INTEGER NOT NULL REFERENCES users(id),
            created_at TEXT NOT NULL, attended_at TEXT, status TEXT NOT NULL DEFAULT 'Pendiente',
            sale_type TEXT NOT NULL DEFAULT 'Mayorista', notes TEXT NOT NULL DEFAULT '',
            weights_json TEXT NOT NULL, price_cents INTEGER NOT NULL, weight_grams INTEGER NOT NULL,
            total_cents INTEGER NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_orders_created ON orders(created_at);
        CREATE INDEX IF NOT EXISTS idx_orders_client ON orders(client_id);
        """)
        db.execute("INSERT OR IGNORE INTO products (name,category,unit,sold_by_weight,price_cents) VALUES ('Huevo comercial','Huevos','kg',1,0)")


init_db()


def now():
    return datetime.now(BUSINESS_TZ).isoformat(timespec="seconds")


def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def password_hash(password: str, salt: str):
    return hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 310000).hex()


def require_user(request: Request):
    token = request.cookies.get("cv_session")
    if not token:
        raise HTTPException(401, "Inicia sesión")
    with database() as db:
        row = db.execute("SELECT users.id, users.username FROM sessions JOIN users ON users.id=sessions.user_id WHERE token_hash=? AND expires_at > ?", (hashlib.sha256(token.encode()).hexdigest(), utc_now())).fetchone()
    if not row:
        raise HTTPException(401, "Sesión vencida")
    return dict(row)


def issue_session(db, response: Response, user_id: int):
    token = secrets.token_urlsafe(32)
    expiry = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(timespec="seconds")
    db.execute("INSERT INTO sessions VALUES (?,?,?)", (hashlib.sha256(token.encode()).hexdigest(), user_id, expiry))
    response.set_cookie("cv_session", token, httponly=True, secure=COOKIE_SECURE, samesite="strict", max_age=604800)


class Credentials(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=10, max_length=200)


class ClientIn(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    document: str = Field(default="", max_length=20)
    phone: str = Field(default="", max_length=25)
    address: str = Field(default="", max_length=200)
    district: str = Field(default="", max_length=100)
    notes: str = Field(default="", max_length=500)


class ProductIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    category: str = Field(default="Abarrotes", max_length=80)
    unit: str = Field(default="unidad", max_length=30)
    sold_by_weight: bool = False
    price: str = "0"


class OrderIn(BaseModel):
    client_id: int
    product_id: int
    weights: list[str | None] = Field(min_length=1, max_length=100)
    price: str
    sale_type: str = Field(default="Mayorista", max_length=40)
    notes: str = Field(default="", max_length=500)


class StatusIn(BaseModel):
    status: str


class WeightsIn(BaseModel):
    weights: list[str] = Field(min_length=1, max_length=100)


def decimal_value(value, minimum=Decimal("0")):
    try:
        number = Decimal(str(value))
        if not number.is_finite() or number < minimum:
            raise ValueError
        return number
    except (InvalidOperation, ValueError):
        raise HTTPException(422, "Número inválido")


def cents(value):
    return int((decimal_value(value) * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def calculate(weights, price_cents):
    if any(w is None for w in weights):
        return 0, 0
    total_grams = int(sum(weights) * 1000)
    total_cents = int(((Decimal(total_grams) / 1000) * Decimal(price_cents)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    return total_grams, total_cents


def parse_weights(values, allow_missing=False):
    weights = [None if allow_missing and (value is None or str(value).strip() == "") else decimal_value(value, Decimal("0.001")) for value in values]
    if any(w is not None and w.as_tuple().exponent < -3 for w in weights):
        raise HTTPException(422, "Usa como máximo tres decimales por jaba")
    return weights


def rowdict(row):
    return dict(row) if row else None


def order_row(db, order_id):
    row = db.execute("""SELECT o.*, c.name client_name, c.phone client_phone, p.name product_name,
        u.username created_by_name FROM orders o JOIN clients c ON c.id=o.client_id
        JOIN products p ON p.id=o.product_id JOIN users u ON u.id=o.created_by
        WHERE o.id=?""", (order_id,)).fetchone()
    if not row:
        raise HTTPException(404, "Pedido no encontrado")
    order = dict(row)
    order["weights"] = json.loads(order.pop("weights_json"))
    return order


@app.get("/")
def index():
    return FileResponse(ROOT / "static" / "index.html")


@app.get("/static/{name}")
def static_file(name: str):
    if name not in ("app.css", "app.js"):
        raise HTTPException(404)
    return FileResponse(ROOT / "static" / name)


@app.get("/api/bootstrap")
def bootstrap(request: Request):
    with database() as db:
        configured = db.execute("SELECT EXISTS(SELECT 1 FROM users)").fetchone()[0] == 1
    user = None
    try:
        user = require_user(request)
    except HTTPException:
        pass
    return {"configured": configured, "user": user}


@app.post("/api/setup")
def setup(data: Credentials, response: Response):
    with database() as db:
        db.execute("BEGIN IMMEDIATE")
        if db.execute("SELECT EXISTS(SELECT 1 FROM users)").fetchone()[0]:
            raise HTTPException(409, "La cuenta inicial ya existe")
        salt = secrets.token_hex(16)
        cur = db.execute("INSERT INTO users(username,password_hash,salt) VALUES (?,?,?)", (data.username.strip(), password_hash(data.password, salt), salt))
        issue_session(db, response, cur.lastrowid)
    return {"ok": True}


@app.post("/api/login")
def login(data: Credentials, response: Response):
    with database() as db:
        user = db.execute("SELECT * FROM users WHERE username=?", (data.username.strip(),)).fetchone()
        valid = user and hmac.compare_digest(password_hash(data.password, user["salt"]), user["password_hash"])
        if not valid:
            raise HTTPException(401, "Usuario o contraseña incorrectos")
        issue_session(db, response, user["id"])
    return {"ok": True}


@app.post("/api/logout")
def logout(request: Request, response: Response):
    token = request.cookies.get("cv_session")
    if token:
        with database() as db:
            db.execute("DELETE FROM sessions WHERE token_hash=?", (hashlib.sha256(token.encode()).hexdigest(),))
    response.delete_cookie("cv_session")
    return {"ok": True}


@app.get("/api/clients")
def clients(request: Request):
    require_user(request)
    with database() as db:
        return [dict(r) for r in db.execute("SELECT * FROM clients ORDER BY name")]


@app.post("/api/clients", status_code=201)
def create_client(data: ClientIn, request: Request):
    require_user(request)
    with database() as db:
        cur = db.execute("INSERT INTO clients(name,document,phone,address,district,notes,created_at) VALUES (?,?,?,?,?,?,?)", (data.name.strip(), data.document.strip(), data.phone.strip(), data.address.strip(), data.district.strip(), data.notes.strip(), now()))
        return rowdict(db.execute("SELECT * FROM clients WHERE id=?", (cur.lastrowid,)).fetchone())


@app.get("/api/products")
def products(request: Request):
    require_user(request)
    with database() as db:
        return [dict(r) for r in db.execute("SELECT * FROM products WHERE active=1 ORDER BY category,name")]


@app.post("/api/products", status_code=201)
def create_product(data: ProductIn, request: Request):
    require_user(request)
    with database() as db:
        try:
            cur = db.execute("INSERT INTO products(name,category,unit,sold_by_weight,price_cents) VALUES (?,?,?,?,?)", (data.name.strip(), data.category.strip(), data.unit.strip(), int(data.sold_by_weight), cents(data.price)))
        except sqlite3.IntegrityError:
            raise HTTPException(409, "El producto ya existe")
        return rowdict(db.execute("SELECT * FROM products WHERE id=?", (cur.lastrowid,)).fetchone())


@app.get("/api/orders")
def orders(request: Request):
    require_user(request)
    with database() as db:
        ids = [r[0] for r in db.execute("SELECT id FROM orders ORDER BY id DESC LIMIT 500")]
        return [order_row(db, i) for i in ids]


@app.post("/api/orders", status_code=201)
def create_order(data: OrderIn, request: Request):
    user = require_user(request)
    with database() as db:
        if not db.execute("SELECT 1 FROM clients WHERE id=?", (data.client_id,)).fetchone():
            raise HTTPException(422, "Cliente no encontrado")
        product = db.execute("SELECT * FROM products WHERE id=? AND active=1", (data.product_id,)).fetchone()
        if not product:
            raise HTTPException(422, "Producto no encontrado")
        weights = parse_weights(data.weights, allow_missing=True)
        if not product["sold_by_weight"]:
            raise HTTPException(422, "Los pedidos por unidad estarán disponibles en una fase posterior")
        price = cents(data.price)
        if price == 0:
            raise HTTPException(422, "Ingresa un precio por kg mayor que cero")
        total_grams, total = calculate(weights, price)
        date = now()
        cur = db.execute("""INSERT INTO orders(client_id,product_id,created_by,created_at,sale_type,notes,weights_json,price_cents,weight_grams,total_cents)
            VALUES (?,?,?,?,?,?,?,?,?,?)""", (data.client_id, data.product_id, user["id"], date, data.sale_type.strip(), data.notes.strip(), json.dumps([str(w) if w is not None else None for w in weights]), price, total_grams, total))
        db.execute("UPDATE orders SET code=? WHERE id=?", (f"PED-{date[:4]}-{cur.lastrowid:05d}", cur.lastrowid))
        return order_row(db, cur.lastrowid)


@app.patch("/api/orders/{order_id}/status")
def update_status(order_id: int, data: StatusIn, request: Request):
    require_user(request)
    allowed = {"Pendiente": {"En preparación", "Cancelado"}, "En preparación": {"Listo", "Cancelado"}, "Listo": {"Atendido", "Cancelado"}}
    with database() as db:
        db.execute("BEGIN IMMEDIATE")
        order = order_row(db, order_id)
        if data.status not in allowed.get(order["status"], set()):
            raise HTTPException(409, "Cambio de estado no permitido")
        if data.status == "Atendido" and any(w is None for w in order["weights"]):
            raise HTTPException(409, "Registra el peso real de todas las jabas antes de atender")
        db.execute("UPDATE orders SET status=?, attended_at=? WHERE id=?", (data.status, now() if data.status == "Atendido" else None, order_id))
        return order_row(db, order_id)


@app.patch("/api/orders/{order_id}/weights")
def update_weights(order_id: int, data: WeightsIn, request: Request):
    require_user(request)
    weights = parse_weights(data.weights)
    with database() as db:
        db.execute("BEGIN IMMEDIATE")
        order = order_row(db, order_id)
        if order["status"] in ("Atendido", "Cancelado"):
            raise HTTPException(409, "No se puede cambiar un pedido cerrado")
        if len(weights) != len(order["weights"]):
            raise HTTPException(422, "Conserva la cantidad de jabas del pedido")
        grams, total = calculate(weights, order["price_cents"])
        db.execute("UPDATE orders SET weights_json=?, weight_grams=?, total_cents=? WHERE id=?", (json.dumps([str(w) for w in weights]), grams, total, order_id))
        return order_row(db, order_id)


@app.get("/api/dashboard")
def dashboard(request: Request):
    require_user(request)
    today = datetime.now(BUSINESS_TZ).date().isoformat()
    with database() as db:
        rows = db.execute("SELECT status,created_at,attended_at,weight_grams,total_cents,weights_json FROM orders").fetchall()
    created = [r for r in rows if r["created_at"].startswith(today)]
    attended = [r for r in rows if r["status"] == "Atendido" and r["attended_at"] and r["attended_at"].startswith(today)]
    return {"orders_today": len(created), "pending": sum(r["status"] not in ("Atendido", "Cancelado") for r in rows), "attended_today": len(attended), "jabas_today": sum(len(json.loads(r["weights_json"])) for r in attended), "kg_today": sum(r["weight_grams"] for r in attended) / 1000, "sales_today_cents": sum(r["total_cents"] for r in attended)}


@app.get("/api/orders/{order_id}/pdf")
def order_pdf(order_id: int, request: Request):
    require_user(request)
    with database() as db:
        order = order_row(db, order_id)
    if order["status"] != "Atendido":
        raise HTTPException(409, "El sustento está disponible al atender el pedido")
    stream = io.BytesIO()
    pdf = canvas.Canvas(stream, pagesize=A4)
    pdf.setTitle(f"Orden de servicio {order['code']}")
    y = 790
    def line(label, size=11, gap=25):
        nonlocal y
        pdf.setFont("Helvetica", size)
        pdf.drawString(50, y, label)
        y -= gap
    line("COMERCIALIZADORA VIVIANA", 17, 38)
    line("ORDEN DE SERVICIO / SUSTENTO INTERNO", 12, 34)
    line(f"N. OS-{order['code'][4:]}")
    line(f"Pedido: {order['code']}")
    line(f"Cliente: {order['client_name']}")
    line(f"Fecha de atencion: {order['attended_at'][:19].replace('T', ' ')}")
    line(f"Producto: {order['product_name']}")
    line(f"Jabas: {len(order['weights'])}")
    for i, weight in enumerate(order["weights"], 1):
        line(f"  Jaba {i}: {weight} kg", 10, 18)
        if y < 120:
            pdf.showPage()
            y = 790
    line(f"Peso total: {order['weight_grams']/1000:.3f} kg")
    line(f"Precio: S/ {order['price_cents']/100:.2f} por kg")
    line(f"TOTAL: S/ {order['total_cents']/100:.2f}", 15, 32)
    line("Estado: ATENDIDO")
    line("Documento interno. No reemplaza boleta ni factura electronica.", 9)
    pdf.save()
    stream.seek(0)
    return StreamingResponse(stream, media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename=OS-{order['code'][4:]}.pdf"})
