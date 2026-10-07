# Comercializadora Viviana

Sistema web para ventas mayoristas de huevo. Permite registrar clientes, productos vendidos por peso y pedidos con una o varias jabas; registrar el peso real de cada jaba; avanzar por los estados de preparación; calcular el total; descargar un sustento interno en PDF; y compartir el resumen por WhatsApp. Incluye un panel con pedidos, ventas y kilos atendidos durante el día.

Es una sola página (`public/index.html`) sobre **Firebase**: Hosting, Authentication (correo y contraseña) y Realtime Database. No hay servidor propio: el navegador habla directo con Firebase y la seguridad la aplican las reglas de `database.rules.json`. Los cambios se ven al instante en todos los equipos conectados.

## Qué hace (v2.10)

- **Vender en 2 pasos:** elegir o crear el cliente; jabas con −/+, peso por jaba y precio por kg con el total en vivo. «Atender ahora» pregunta **¿Cómo pagó?**: Efectivo, Yape/Plin, Transferencia (un toque) o Fiado, con lo que dejó a cuenta.
- **Pedidos:** Pendiente → En preparación → Listo → Atendido. Un pedido pendiente se atiende con el mismo selector de pago. Cancelar o anular pide motivo; nada se borra.
- **Cobros:** saldo por cliente (ventas fiadas menos pagos), «Registrar pago» con recibo por WhatsApp, «Recordar por WhatsApp» con el detalle de notas pendientes, cobrado hoy por medio de pago y pagos anulables con motivo. Lo dejado a cuenta al vender se aplica a esa nota y el resto de los pagos a las notas más antiguas.
- **Nota de pedido:** PDF con los datos del negocio y enlace público de solo lectura (`/?nota=TOKEN`) que se envía por WhatsApp en dos toques.
- **Productos** con precio semanal e historial; **clientes** editables; **usuarios** con roles admin/ventas.
- **App instalable** en el celular (Más → Instalar en el celular).

## Cómo seguimos mejorando

1. **Usar y anotar.** Durante la semana, anota lo que molesta o falta (con captura si se puede).
2. **Pedir el cambio.** Una cosa por pedido, contando el problema real («mi mamá no encuentra…»), no solo la solución.
3. **Construir y probar.** Cada cambio se prueba en los emuladores (`firebase emulators:start --project demo-comercializadora`), sube `APP_VERSION` y agrega una entrada al `CHANGELOG`.
4. **Publicar.** `git pull` y `firebase deploy --only database,hosting`; comprobar la versión en la barra lateral.
5. **Revisar con ella.** Ver a tu mamá usarlo unos minutos; ahí aparecen los siguientes cambios.

### Próximas mejoras

| Prioridad | Mejora | Para qué |
|---|---|---|
| Alta | Repetir último pedido | Clientes fijos en un toque |
| Alta | Cierre del día por WhatsApp | Resumen diario de ventas, cobros y fiado |
| Media | Ingreso de mercadería semanal | Stock, costo y ganancia por semana |
| Media | Exportar a Excel | Contador y respaldo |
| Media | Modo letra grande | Lectura más cómoda |
| Por definir | Tara de la jaba | Solo si el precio por kg no debe incluir el peso de la jaba |

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
