# Tienda Gemer Profesional

Proyecto web completo para una tienda gamer, desarrollado con **Flask + SQLite + HTML + CSS + JavaScript**.

## Funciones incluidas

- Página principal responsive y catálogo profesional.
- Buscador, filtros y ordenamiento de productos.
- Fichas de producto con color, cantidad y compra directa.
- Carrito funcional con actualización y eliminación de productos.
- Registro, inicio y cierre de sesión con contraseñas cifradas.
- Checkout con datos de entrega y métodos de pago.
- Historial de compras y boletas imprimibles en PDF.
- Dashboard administrativo con métricas, gráficos, pedidos, inventario, clientes y mensajes.
- Cambio del estado de pedidos y actualización de stock.
- Base de datos SQLite creada automáticamente.
- Configuración lista para Render como Web Service.


## Inicio rápido en Windows

No abras directamente `templates/index.html`, porque es una plantilla Jinja que necesita Flask.

Haz doble clic en:

```text
1_INICIAR_TIENDA.bat
```

El archivo comprueba Python, instala las dependencias si faltan, inicia Flask y abre el navegador automáticamente.

## Abrir en Visual Studio Code

1. Descomprime el ZIP.
2. En VS Code entra a **Archivo > Abrir carpeta**.
3. Selecciona la carpeta `tienda-gemer`.
4. Abre la terminal integrada.
5. Ejecuta:

```bash
python -m venv venv
```

En Windows activa el entorno:

```bash
venv\Scripts\activate
```

Instala las dependencias:

```bash
pip install -r requirements.txt
```

Ejecuta el proyecto:

```bash
python app.py
```

Abre en el navegador:

```text
http://127.0.0.1:5000
```

## Cuentas de demostración

Administrador:

```text
Correo: admin@tiendagemer.pe
Contraseña: Admin123!
```

Cliente:

```text
Correo: cliente@tiendagemer.pe
Contraseña: Cliente123!
```

## Publicar en Render

Este proyecto tiene backend, por lo que se publica como **Web Service**, no como Static Site.

Configuración manual:

```text
Runtime: Python 3
Build Command: pip install -r requirements.txt
Start Command: gunicorn app:app
```

También puedes usar el archivo `render.yaml` incluido mediante **New > Blueprint**.

> Nota: SQLite funciona bien para la demostración académica. En el plan gratuito de Render, los datos nuevos pueden reiniciarse después de un redespliegue o reinicio. Para producción real se recomienda PostgreSQL.

## Estructura

```text
tienda-gemer/
├── app.py
├── requirements.txt
├── render.yaml
├── Procfile
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── explore.html
│   ├── product_detail.html
│   ├── cart.html
│   ├── checkout.html
│   ├── login.html
│   ├── register.html
│   ├── purchases.html
│   ├── receipt.html
│   ├── admin.html
│   └── error.html
└── static/
    ├── css/style.css
    ├── js/app.js
    ├── js/admin.js
    └── img/
```
