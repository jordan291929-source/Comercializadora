# Historial de cambios

Registro de todos los cambios del sistema, del más reciente al más antiguo. Cada entrada indica la fecha, qué cambió y por qué.

## 2026-11-11 — Corrección de pedidos con motivo

**Motivo:** cuando había un error en un pedido (incluso ya atendido), la única opción era cancelarlo y registrarlo de nuevo. Eso duplicaba pedidos y dejaba cancelaciones que no eran reales.

**Cambios:**
- Nuevo botón **✎ Editar** en el detalle de cualquier pedido que no esté cancelado, incluidos los **atendidos**.
- Se puede corregir el cliente, el producto, el tipo de venta, el precio por kg, las observaciones, el peso de cada jaba y la cantidad de jabas (agregar o quitar).
- El **motivo de la corrección es obligatorio** (de 5 a 300 caracteres).
- Cada corrección queda guardada en la nueva tabla `order_edits` con la fecha, el usuario, el motivo, la lista legible de cambios (por ejemplo, «Total: S/ 352.75 → S/ 542.08») y una copia del pedido antes y después.
- El detalle del pedido muestra el **Historial de correcciones**, y la lista de pedidos marca «✎ Corregido».
- El PDF de un pedido corregido indica cuántas correcciones tuvo, la fecha de la última y su motivo.
- Reglas:
  - Un pedido atendido no puede quedar con pesos pendientes.
  - No se guarda una corrección sin cambios.
  - Los pedidos cancelados no se editan.
  - La fecha de atención original se conserva.
- API: `PUT /api/orders/{id}` (requiere `reason`) y `GET /api/orders/{id}/edits`.
- La tabla nueva se crea sola al iniciar. No hace falta migrar los datos existentes.

## 2026-10-07 — Título y descripción del README
- Se actualizó el nombre del proyecto y la descripción general del sistema.

## 2026-10-07 — Despliegue web protegido y persistente
- Se agregó `render.yaml` para publicar en Render con un disco persistente para la base de datos SQLite.
- Se agregó una clave de instalación (`COMERCIALIZADORA_SETUP_KEY`) que protege la creación de la primera cuenta cuando el sitio es público.
- Se agregaron cookies seguras (`COMERCIALIZADORA_SECURE_COOKIE`) para HTTPS.

## 2026-10-07 — Primera fase del sistema de pedidos de huevo
- Registro de clientes, productos vendidos por peso y pedidos con una o varias jabas.
- Registro del peso real por jaba y cálculo del total sobre la suma real.
- Estados: Pendiente → En preparación → Listo → Atendido, más Cancelado.
- PDF de sustento interno, envío del resumen por WhatsApp y panel del día (pedidos, ventas y kilos).
