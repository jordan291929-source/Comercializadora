# Comercializadora Viviana

Primera fase de un sistema web para ventas mayoristas de huevo. Permite registrar clientes, productos vendidos por peso y pedidos con una o varias jabas; registrar el peso real de cada jaba; avanzar por los estados de preparación; calcular el total; descargar un sustento interno en PDF; y compartir el resumen por WhatsApp. Incluye un panel con pedidos, ventas y kilos atendidos durante el día.

## Flujo de trabajo

1. Se registra el cliente y el precio por kg del pedido.
2. Se indica cuántas jabas pidió. Los pesos pueden quedar pendientes si todavía no se preparó la mercadería.
3. Al pesar las jabas, se registran los pesos reales. El total se calcula sobre su suma, sin asumir un peso promedio fijo.
4. El pedido pasa por **Pendiente → En preparación → Listo → Atendido**. No se puede atender mientras falte algún peso. También se puede cancelar antes de atender.
5. La atención fija la fecha y hora, habilita el PDF interno y el mensaje de WhatsApp. El pedido atendido no puede modificarse.

El sustento interno no es una boleta o factura electrónica. La salida de inventario se agregará cuando exista un módulo de stock, para que la atención la registre una sola vez y evite doble digitación. El enlace de WhatsApp comparte texto; el PDF se descarga desde el pedido y puede adjuntarse manualmente.

## Ejecutar

Requiere Python 3.12. Desde la raíz del repositorio:

```sh
python -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn app:app --host 127.0.0.1 --port 8000
```

Abre la aplicación en el navegador y crea la cuenta inicial. La contraseña debe tener al menos 10 caracteres. La base de datos SQLite se crea en `data/app.sqlite3` y se excluye de Git. Haz copias de seguridad periódicas de ese archivo. Para una instalación accesible desde Internet se necesita HTTPS, establecer `COMERCIALIZADORA_SECURE_COOKIE=1` y un servicio con almacenamiento persistente. El archivo SQLite permite un despliegue pequeño de una sola instancia; una futura versión multiinstancia requerirá migrar la capa de datos a PostgreSQL.

En Windows, usa `py -m venv .venv`, `.venv\Scripts\python -m pip install -r requirements.txt` y `.venv\Scripts\python -m uvicorn app:app --host 127.0.0.1 --port 8000`. La dependencia `tzdata` proporciona la zona horaria de Perú en instalaciones de Windows que no la incluyen.

Para pruebas aisladas, `COMERCIALIZADORA_DB=/ruta/temporal.sqlite3` cambia la ubicación de la base de datos. No guardes credenciales en el repositorio.

## Decisiones y siguientes fases

- El precio por kg se fija en cada pedido. El monto final queda pendiente hasta registrar todos los pesos. Así no se cobra un estimado como si fuera peso real.
- Esta fase admite productos vendidos por peso. El catálogo deja preparados nombre, categoría y unidad; las ventas por unidad se habilitarán junto con abarrotes.
- Fase 2: ingresos y salidas de inventario, proveedores y costos. La salida debe generarse de forma idempotente al atender un pedido y descontar tanto jabas como kilos.
- Fase 3: OCR de comprobantes de compra con revisión humana obligatoria antes de generar un ingreso.
- Fase 4: reportes de margen, cuentas por cobrar, permisos de usuario y abarrotes.

Antes de usar inventario en producción hay que definir si el peso registrado es neto de huevo o incluye la tara de la jaba, y cómo se contabilizan las jabas retornables. Los importes actuales usan el peso ingresado tal como se registra.
