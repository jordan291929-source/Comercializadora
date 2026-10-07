# Comercializadora Viviana

Sistema web para ventas mayoristas de huevo. Permite registrar clientes, productos vendidos por peso y pedidos con una o varias jabas; registrar el peso real de cada jaba; avanzar por los estados de preparación; calcular el total; descargar un sustento interno en PDF; y compartir el resumen por WhatsApp. Incluye un panel con pedidos, ventas y kilos atendidos durante el día.

Es una sola página (`public/index.html`) sobre **Firebase**: Hosting, Authentication (correo y contraseña) y Realtime Database. No hay servidor propio: el navegador habla directo con Firebase y la seguridad la aplican las reglas de `database.rules.json`. Los cambios se ven al instante en todos los equipos conectados.

## Flujo de trabajo

1. Se registra el cliente y el precio por kg del pedido.
2. Se indica cuántas jabas pidió. Los pesos pueden quedar pendientes si todavía no se preparó la mercadería.
3. Al pesar las jabas, se registran los pesos reales. El total se calcula sobre su suma, sin asumir un peso promedio fijo.
4. El pedido pasa por **Pendiente → En preparación → Listo → Atendido**. No se puede atender mientras falte algún peso. También se puede cancelar antes de atender.
5. La atención fija la fecha y hora, habilita el PDF interno y el mensaje de WhatsApp. El pedido atendido o cancelado no puede modificarse ni borrarse (lo impiden las reglas de la base de datos).

El sustento interno no es una boleta o factura electrónica. El enlace de WhatsApp comparte texto; el PDF se descarga desde el pedido y puede adjuntarse manualmente.

## Usuarios y roles

- Cualquiera puede crear una cuenta, pero queda **sin acceso** («Cuenta pendiente de aprobación») hasta que el administrador le asigne un rol en la pestaña **Usuarios**.
- **La primera cuenta que se crea en el proyecto queda como dueña y administradora.** Créala apenas publiques el sitio.
- Roles: `admin` (todo, más gestionar usuarios) y `ventas` (clientes, productos y pedidos).

## Crear el proyecto en Firebase (una sola vez)

Se usa el plan gratuito Spark; no necesita tarjeta.

1. En https://console.firebase.google.com crea un proyecto nuevo. El ID sugerido es `comercializadora-viviana`; si Firebase te da otro, cámbialo en `.firebaserc`.
2. **Authentication → Comenzar → Correo electrónico/contraseña → Habilitar.**
3. **Realtime Database → Crear base de datos →** ubicación `us-central1`, **modo bloqueado** (las reglas reales se suben con el deploy).
4. **Configuración del proyecto → Tus apps → Agregar app → Web (`</>`)**, con cualquier apodo. No hace falta copiar la configuración: Firebase Hosting la entrega sola en `/__/firebase/init.json`.

## Publicar

Requiere Node.js y Firebase CLI (`npm install -g firebase-tools`). Desde la raíz del repositorio:

```sh
firebase login
firebase deploy --only database,hosting
```

Queda en `https://<id-del-proyecto>.web.app`. Después de cada deploy, recarga con Ctrl+F5.

## Probar en local (emuladores)

```sh
firebase emulators:start --project demo-comercializadora
```

Abre http://127.0.0.1:5000. Desde `localhost` la app se conecta sola a los emuladores de Auth y Database, con las mismas reglas; no toca los datos reales.

## Convenciones

- Cada cambio sube `APP_VERSION` en `public/index.html` y agrega una entrada al inicio de `CHANGELOG`. La versión se ve en la barra lateral; al pulsarla se muestran las novedades.
- Los montos se guardan en céntimos y los pesos en gramos, como enteros, para evitar errores de redondeo.
- Hora del negocio: America/Lima (UTC-5).

## Copias de seguridad

El plan gratuito no tiene respaldos automáticos. Exporta la base periódicamente desde **Realtime Database → ⋮ → Exportar JSON** y guarda el archivo en un lugar seguro.

## Decisiones y siguientes fases

- El precio por kg se fija en cada pedido. El monto final queda pendiente hasta registrar todos los pesos. Así no se cobra un estimado como si fuera peso real.
- Esta fase admite productos vendidos por peso. El catálogo deja preparados nombre, categoría y unidad; las ventas por unidad se habilitarán junto con abarrotes.
- Fase 2: ingresos y salidas de inventario, proveedores y costos. La salida debe generarse una sola vez al atender un pedido y descontar tanto jabas como kilos.
- Fase 3: OCR de comprobantes de compra con revisión humana obligatoria antes de generar un ingreso.
- Fase 4: reportes de margen, cuentas por cobrar y abarrotes.

Antes de usar inventario en producción hay que definir si el peso registrado es neto de huevo o incluye la tara de la jaba, y cómo se contabilizan las jabas retornables. Los importes actuales usan el peso ingresado tal como se registra.
