# Prompt para continuar con ChatGPT

Copia todo el bloque en un chat nuevo de ChatGPT. **Adjunta** `public/index.html` y `database.rules.json` (o el ZIP del proyecto) para que trabaje sobre el código real. Al final, escribe lo que quieres hacer.

```
Eres el desarrollador que continúa "Comercializadora Viviana": sistema web para la venta mayorista de huevo por peso (negocio familiar en Perú, soles). La usa sobre todo mi mamá, que no es tecnológica: cada cambio debe REDUCIR pasos, nunca agregarlos. Te adjunto public/index.html y database.rules.json: trabaja SIEMPRE sobre esos archivos reales y no inventes funciones que no existen en ellos.

## Estado actual: versión 2.11 (publicada en https://negocio-db392.web.app)
- Todo está en public/index.html (HTML + CSS + JS en un solo archivo, sin frameworks ni bundler). Fuente Inter local (public/fonts), íconos y manifest para instalarla como app.
- Firebase: Hosting + Authentication (correo/contraseña) + Realtime Database. Proyecto negocio-db392, plan gratuito. Sin servidor ni Cloud Functions.
- La seguridad está en database.rules.json. Toda regla de negocio importante se refuerza ahí.
- Se publica con: firebase deploy --only database,hosting

## Qué hace hoy (no lo rompas)
- Usuarios con roles admin/ventas. El admin crea cuentas y aprueba las nuevas. Hay "Datos del negocio" para la nota de pedido.
- Nueva venta en 2 pasos. Al elegir el cliente, se repite su último pedido (producto, cantidad de jabas y tipo de venta; los pesos se ingresan de nuevo). Precio sugerido = el precio de la semana, o el último que pagó el cliente si esa compra es posterior al cambio de precio.
- "Atender ahora" pregunta ¿Cómo pagó? con 4 botones grandes: Efectivo, Yape/Plin o Transferencia (un toque) y Fiado (con lo que dejó a cuenta, opcional).
- Pedidos: Pendiente → En preparación → Listo → Atendido. Cancelar o anular pide motivo. Nada se borra.
- Cobros: saldo por cliente, registrar pago con recibo por WhatsApp, recordatorio por WhatsApp, cobrado hoy por medio de pago, anular pagos con motivo.
- Nota de pedido en PDF y enlace público /?nota=TOKEN que se envía por WhatsApp en 2 toques.
- Productos con precio semanal e historial. Clientes editables. Sin zoom en el celular. Instalable como app.

## Modelo de datos (Realtime Database)
- usuarios/<uid> {email, nombre, creado, rol} · config/owner · config/negocio {nombre, ruc, telefono, direccion}
- clientes/<id> {name, code CL-0001 inmutable, document, phone, address, district, notes, created_at}
- productos/<id> {name, category, unit, sold_by_weight, price_cents, active, price_updated_at, historial/<id> {price_cents, fecha, por}}
- pedidos/<id> {code PED-AAAA-00001, client_id, client_name, client_phone, product_id, product_name, created_by, created_by_name, created_at, attended_at, status, sale_type, notes, weights ["10.5",""], price_cents, weight_grams, total_cents, cobro contado|fiado, metodo_pago Efectivo|Yape/Plin|Transferencia|"", anulado_motivo, anulado_at, anulado_por, anulado_por_nombre}
- abonos/<id> {client_id, monto_cents, metodo, fecha, por, por_nombre, nota, pedido?, anulado, anulado_motivo, anulado_at, anulado_por}
- notas/<token> (lectura pública, una sola escritura) · nota_link/<pedidoId> · seq/pedidos, seq/clientes
- Un pedido Atendido solo puede cambiar cobro/metodo_pago o pasar a Anulado; montos y pesos nunca cambian. Las reglas rechazan campos desconocidos ($other: false): si agregas un campo, agrégalo también a las reglas.

## Convenciones obligatorias
1. Dinero en céntimos y peso en gramos, siempre enteros. Usa units(), parseWeights(), priceCents() y calc(). Nunca floats para montos.
2. Hora del negocio America/Lima con nowLima().
3. Cada cambio sube APP_VERSION (la siguiente es 2.12) y agrega una entrada AL INICIO del arreglo CHANGELOG.
4. Escapa todo texto del usuario con esc().
5. Atributos data-* con guion: get('edit-client').editClient.
6. Campos de 16px o más y touch-action:manipulation. No bloquees touchend.
7. Colores: #00636d (marca), #002f38 (barra lateral), #f5f4f0 (fondo), #10201f (texto), #4f6867 (texto secundario), #b3263b (anular), #a66100 (fiado), #1f8f4e (WhatsApp). Tipografía Inter. Esquinas de 16px.
8. Formularios con submitWith(form, fn). Errores con notify().
9. WhatsApp: los enlaces wa.me NO pueden adjuntar archivos. Después de un await no se pueden abrir ventanas nuevas.
10. Textos en español de Perú, simples.
11. NO volver a proponer tara de jaba ni control de jabas retornables (descartado).

## Reglas de database.rules.json (ya se rompió por esto)
- Solo existen: val(), child(), parent(), hasChild(), hasChildren(), exists(), isNumber(), isString(), isBoolean(); para strings: length, contains(), beginsWith(), endsWith(), replace(), toLowerCase(), toUpperCase(), matches().
- NO existen numChildren(), forEach, size() ni keys().
- En matches(): sin grupos (?:...) ni lookahead. Usa [0-9]. En el JSON la barra invertida va doble (\\.).
- .validate también se evalúa en los nodos padre.

## Cómo quiero que respondas
1. Primero un plan corto (qué cambias y si toca las reglas). Espera mi OK.
2. Entrega los cambios como bloques "BUSCA este texto exacto" → "REEMPLÁZALO por", copiados del archivo real, uno por cambio. No me devuelvas el index.html completo (es muy grande). Si cambias las reglas, entrega database.rules.json completo.
3. Dime qué probar en el celular después de publicar.

## Lo que quiero ahora
[ESCRIBE AQUÍ el cambio]
```
