# Comercializadora Viviana — contexto para Claude

Sistema de ventas mayoristas de huevo por peso (negocio familiar en Perú, soles). Lo usa principalmente la mamá de Jordan, que no es tecnológica: **cada cambio debe reducir pasos, no agregarlos.** Habla con Jordan en español, directo y sin jerga.

## Arquitectura

- Todo en `public/index.html` (HTML + CSS + JS, sin frameworks ni bundler). Fuente Inter local en `public/fonts/`, íconos y `manifest.webmanifest` para instalarla como app.
- Firebase: Hosting + Authentication (correo/contraseña) + Realtime Database. Proyecto `negocio-db392` (plan Spark), URL https://negocio-db392.web.app. Sin servidor ni Cloud Functions.
- Seguridad en `database.rules.json`. Toda regla de negocio importante se refuerza ahí.
- La configuración de Firebase se lee de `/__/firebase/init.json`. En localhost la app usa los emuladores.
- **Publicación automática** (autorizada por Jordan): cada push a `claude/nice-brahmagupta-at5kbl` o `main` publica en negocio-db392 vía `.github/workflows/deploy.yml` (secreto `FIREBASE_SERVICE_ACCOUNT`). Subir = publicar en vivo: prueba en el emulador ANTES de cada push y revisa que el run termine en «Deploy complete!».

## Modelo de datos

- `usuarios/<uid>`: {email, nombre, creado, rol: admin|ventas}. `config/owner`: la primera cuenta, que es admin. `config/negocio`: datos para la nota de pedido.
- `clientes/<id>` (code CL-0001 inmutable), `productos/<id>` (price_cents semanal, price_updated_at, historial inmutable, active).
- `pedidos/<id>`: code PED-AAAA-00001, client_id, weights ["10.5", ""], price_cents, weight_grams, total_cents, status Pendiente→En preparación→Listo→Atendido (se puede atender directo), Cancelado / Anulado (con anulado_motivo/at/por), cobro contado|fiado, metodo_pago Efectivo|Yape/Plin|Transferencia, jabas (cantidad; con «peso total» weights tiene un solo valor), peso_pendiente:true (atendido sin pesar; se pesa después y recién ahí se crea la nota).
- `abonos/<id>`: pagos de clientes (client_id, monto_cents, metodo, fecha, por, pedido opcional = a cuenta). Solo se escriben una vez; se pueden anular con motivo.
- `notas/<token>` (lectura pública por token, una sola escritura) y `nota_link/<pedidoId>`: nota de pedido que se manda por WhatsApp como enlace `/?nota=TOKEN`.
- `seq/pedidos`, `seq/clientes`: contadores que suben de 1 en 1.
- `ingresos/<id>`: conteo de jabas que llegan del proveedor {fecha, proveedor, min_g, max_g, nota, creado, por, por_nombre, cerrado}; `jabas/<pushId>` {g, hora, por}. Cada jaba con push() (varios celulares a la vez); anotar NO espera al servidor. Cerrado = solo lectura; solo admin reabre. No se conecta con ventas.
- Nada se borra. Un pedido atendido solo cambia cobro/metodo_pago, se pesa una vez si tenía peso_pendiente, o pasa a Anulado.
- Venta: los botones de pago CIERRAN la venta (un toque). WhatsApp se abre en ese mismo toque si el interruptor está activo; la venta se guarda detrás (`finishSale`). El peso es opcional.
- Saldo del cliente = ventas fiadas atendidas − abonos no anulados. Lo dejado a cuenta va a su propia nota; el resto, a las notas más antiguas (`ledger()`).

## Convenciones

1. Dinero en céntimos y peso en gramos, siempre enteros. Usa `units()`, `parseWeights()`, `priceCents()` y `calc()`. Nunca floats.
2. Hora del negocio America/Lima (UTC-5) con `nowLima()`.
3. Cada cambio sube `APP_VERSION` y agrega una entrada AL INICIO de `CHANGELOG`.
4. Escapa todo texto del usuario con `esc()`.
5. Atributos data-* con guion: `get('edit-client').editClient`.
6. Campos de 16px o más y `touch-action:manipulation` (sin zoom en iPhone). No bloquees touchend.
7. Colores: #00636d (marca), #002f38 (barra lateral), #f5f4f0 (fondo), #10201f (texto), #4f6867 (texto secundario), #b3263b (anular), #a66100 (fiado), #1f8f4e (WhatsApp).
8. Formularios con `submitWith(form, fn)`, errores con `notify()`.
9. WhatsApp: los enlaces `wa.me` no pueden adjuntar archivos. Por eso la nota se manda como enlace.
10. Después de un `await` no se pueden abrir ventanas nuevas: prepara los enlaces antes o usa `location.href`.

## Reglas de Realtime Database (ya se rompieron por esto)

- Solo existen: val(), child(), parent(), hasChild(), hasChildren(), exists(), isNumber(), isString(), isBoolean(), y para strings length, contains(), beginsWith(), endsWith(), replace(), toLowerCase(), toUpperCase() y matches().
- **No existen** numChildren(), forEach, size() ni keys().
- En matches() **no uses** grupos `(?:…)` ni lookahead. Usa `[0-9]` y en el JSON escribe `\\.`.
- `.validate` también se evalúa en los nodos padre. En escrituras multi-ruta, `newData.parent()…` ve el estado nuevo.
- Si el emulador dice "No such method/property" o "Failed to load…rules", el cambio no está listo.

## Cómo probar

```sh
firebase emulators:start --project demo-comercializadora   # http://127.0.0.1:5000
```

- Prueba con Playwright en viewport de celular (390×844).
- Oculta `.firebase-emulator-warning`, porque tapa la barra inferior.
- Revisa la sintaxis del script con `node --check` después de extraerlo de index.html.
- Siempre prueba: venta con «Atender ahora» → ¿Cómo pagó? (contado y fiado con a cuenta), pedido pendiente → registrar peso → atender, anular, registrar y anular un pago, enlace de la nota abierto sin sesión, y los intentos que las reglas deben denegar.

## Flujo con ChatGPT (acordado con Jordan)

ChatGPT construye los cambios con `docs/PROMPT_CHATGPT.md`. **Nada se publica sin pasar por Claude**: Jordan trae los bloques o archivos de ChatGPT («revisa las actualizaciones»), Claude los aplica o revisa, prueba en el emulador, corrige y sube a GitHub, lo que publica automáticamente. Sé breve y económico: Jordan cuida el gasto de tokens.

## Pendientes acordados (en orden)

Meta de Jordan: que su mamá aprenda de a poco y registre todo, para que el negocio quede automatizado. Cada paso nuevo debe ser simple y sin romper lo anterior.

1. ✅ Ingresos de OTROS productos (v2.21): ingresos/<id>.tipo 'huevo'|'otros' (sin tipo = huevo); items/<pushId> {producto, cantidad, unidad saco|bolsa|caja|paquete|unidad, costo_cents?, hora, por}.
2. ✅ Venta por unidad (v2.22): productos sold_by_weight:false con unit saco|bolsa|caja|paquete|unidad; pedidos por_unidad:true, unidad, cantidad, price_cents unitario, total = cantidad × precio, weight_grams 0, sin weights/jabas. Chips de producto en la venta solo si hay más de uno activo; el huevo siempre primero y preseleccionado.
3. **Lector de documentos (no olvidar):** foto de la factura o guía del proveedor → la app lee proveedor, productos, cantidades y costos → la mamá revisa y confirma → se crea el ingreso. Revisión humana obligatoria antes de guardar. Necesita un servicio de IA con clave secreta (no puede ir en el navegador): requiere Cloud Functions (plan Blaze, pago por uso) o un servicio externo; costo por documento de céntimos. Decidir con Jordan antes de construir.
4. Stock: que ingresos y ventas muevan el inventario (después de 1 y 2).
5. ✅ Caja del día (v2.29): página `caja` con vendido, cobrado por medio, fiado por cliente, últimos 7 días, selector de día y cierre por WhatsApp (`dayFinance()`, `cierreMessage()`). Pendiente: exportar a Excel, modo letra grande.
6. Diseño, pantalla por pantalla: ✅ Inicio + cabecera con logo y panel de usuario (v2.24). ✅ Pedidos agrupados por día con filas compactas y botón Atender/Pesar (v2.25). ✅ Cobros con resumen del día, deudores con Recordar/Cobrar y pagos anulables (v2.26). ✅ Clientes con buscador, últimas compras, saldo y botones Escribir/Vender (v2.27). ✅ Detalle del pedido con total grande, botón principal según el caso y «Cobrar» si debe (v2.28).
- **Descartado:** tara de la jaba y control de jabas retornables (las jabas se van con el cliente y se cobra el peso de la balanza). No volver a proponerlo.
