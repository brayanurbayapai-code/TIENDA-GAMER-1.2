from __future__ import annotations

import os
import sqlite3
import threading
import webbrowser
from datetime import datetime, timedelta
from functools import wraps
from pathlib import Path
from typing import Any

from flask import (
    Flask,
    abort,
    flash,
    g,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash

BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = Path(os.getenv("DATABASE_PATH", BASE_DIR / "tienda_gemer.db"))

app = Flask(
    __name__,
    template_folder=str(BASE_DIR / "templates"),
    static_folder=str(BASE_DIR / "static"),
)
app.config.update(
    SECRET_KEY=os.getenv("SECRET_KEY", "tienda-gemer-dev-change-me"),
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    MAX_CONTENT_LENGTH=2 * 1024 * 1024,
)

PRODUCT_SEED = [
    {
        "slug": "mouse-rgb",
        "name": "Mouse RGB Storm X",
        "category": "Mouse RGB",
        "description": "Sensor óptico de alta precisión, 7 botones programables e iluminación RGB personalizable.",
        "price": 89.90,
        "old_price": 109.90,
        "image": "img/mouse.svg",
        "stock": 28,
        "badge": "Más vendido",
        "specs": "Hasta 12,000 DPI|7 botones programables|Iluminación RGB|Cable trenzado de 1.8 m",
    },
    {
        "slug": "mouse-inalambrico",
        "name": "Mouse Wireless Nova",
        "category": "Inalámbrico",
        "description": "Conexión estable de baja latencia, batería recargable y diseño ergonómico para largas sesiones.",
        "price": 129.90,
        "old_price": 149.90,
        "image": "img/mouse.svg",
        "stock": 16,
        "badge": "Recomendado",
        "specs": "Conexión 2.4 GHz|Batería de hasta 70 horas|Hasta 10,000 DPI|Peso ligero",
    },
    {
        "slug": "mouse-pro-x",
        "name": "Mouse Pro X Elite",
        "category": "Competitivo",
        "description": "Mouse ultraligero para esports, sensor profesional y switches de respuesta inmediata.",
        "price": 169.90,
        "old_price": 199.90,
        "image": "img/mouse.svg",
        "stock": 10,
        "badge": "Pro",
        "specs": "Sensor de 16,000 DPI|Peso de 62 g|Memoria integrada|Switches de alta duración",
    },
    {
        "slug": "teclado-tkl",
        "name": "Teclado Strike TKL",
        "category": "Teclado",
        "description": "Teclado mecánico compacto con switches lineales, anti-ghosting y retroiluminación RGB.",
        "price": 249.90,
        "old_price": 289.90,
        "image": "img/keyboard.svg",
        "stock": 14,
        "badge": "Nuevo",
        "specs": "Formato TKL|Switches lineales|Anti-ghosting completo|Cable USB-C desmontable",
    },
    {
        "slug": "auriculares-7-1",
        "name": "Auriculares Vortex 7.1",
        "category": "Audio",
        "description": "Sonido envolvente, micrófono desmontable y almohadillas cómodas para streaming y gaming.",
        "price": 219.90,
        "old_price": 259.90,
        "image": "img/headset.svg",
        "stock": 12,
        "badge": "-15%",
        "specs": "Audio virtual 7.1|Micrófono desmontable|Control de volumen|Almohadillas memory foam",
    },
    {
        "slug": "monitor-144hz",
        "name": "Monitor Vision 24\" 144 Hz",
        "category": "Monitor",
        "description": "Panel IPS Full HD, respuesta de 1 ms y sincronización adaptativa para una imagen fluida.",
        "price": 899.90,
        "old_price": 999.90,
        "image": "img/monitor.svg",
        "stock": 7,
        "badge": "Stock limitado",
        "specs": "24 pulgadas Full HD|144 Hz|1 ms de respuesta|Adaptive Sync",
    },
]


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
        g.db = sqlite3.connect(DATABASE_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(_: BaseException | None) -> None:
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db() -> None:
    db = sqlite3.connect(DATABASE_PATH)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'customer',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slug TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            description TEXT NOT NULL,
            price REAL NOT NULL CHECK(price >= 0),
            old_price REAL,
            image TEXT NOT NULL,
            stock INTEGER NOT NULL DEFAULT 0 CHECK(stock >= 0),
            badge TEXT,
            specs TEXT,
            active INTEGER NOT NULL DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            order_number TEXT UNIQUE,
            total REAL NOT NULL,
            status TEXT NOT NULL DEFAULT 'Confirmado',
            payment_method TEXT NOT NULL,
            customer_name TEXT NOT NULL,
            dni TEXT NOT NULL,
            customer_email TEXT NOT NULL,
            phone TEXT NOT NULL,
            department TEXT NOT NULL,
            city TEXT NOT NULL,
            district TEXT NOT NULL,
            address TEXT NOT NULL,
            notes TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            product_name TEXT NOT NULL,
            price REAL NOT NULL,
            quantity INTEGER NOT NULL,
            color TEXT,
            subtotal REAL NOT NULL,
            FOREIGN KEY(order_id) REFERENCES orders(id) ON DELETE CASCADE,
            FOREIGN KEY(product_id) REFERENCES products(id)
        );

        CREATE TABLE IF NOT EXISTS contact_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        """
    )

    for product in PRODUCT_SEED:
        db.execute(
            """
            INSERT INTO products
                (slug, name, category, description, price, old_price, image, stock, badge, specs)
            VALUES
                (:slug, :name, :category, :description, :price, :old_price, :image, :stock, :badge, :specs)
            ON CONFLICT(slug) DO UPDATE SET
                name=excluded.name,
                category=excluded.category,
                description=excluded.description,
                price=excluded.price,
                old_price=excluded.old_price,
                image=excluded.image,
                badge=excluded.badge,
                specs=excluded.specs
            """,
            product,
        )

    admin_email = os.getenv("ADMIN_EMAIL", "admin@tiendagemer.pe").strip().lower()
    admin_password = os.getenv("ADMIN_PASSWORD", "Admin123!")
    demo_email = "cliente@tiendagemer.pe"

    db.execute(
        """
        INSERT INTO users (name, email, password_hash, role)
        VALUES (?, ?, ?, 'admin')
        ON CONFLICT(email) DO UPDATE SET role='admin'
        """,
        ("Administrador Tienda Gemer", admin_email, generate_password_hash(admin_password)),
    )
    db.execute(
        """
        INSERT INTO users (name, email, password_hash, role)
        VALUES (?, ?, ?, 'customer')
        ON CONFLICT(email) DO NOTHING
        """,
        ("Cliente Demo", demo_email, generate_password_hash("Cliente123!")),
    )
    db.commit()

    total_orders = db.execute("SELECT COUNT(*) AS total FROM orders").fetchone()["total"]
    if total_orders == 0:
        user = db.execute("SELECT id FROM users WHERE email = ?", (demo_email,)).fetchone()
        products = db.execute("SELECT * FROM products ORDER BY id LIMIT 5").fetchall()
        statuses = ["Entregado", "Enviado", "Preparando", "Confirmado", "Entregado"]
        quantities = [2, 1, 1, 3, 1]
        now = datetime.now()
        for index, product in enumerate(products):
            quantity = quantities[index]
            total = round(float(product["price"]) * quantity, 2)
            date = (now - timedelta(days=(4 - index) * 2)).strftime("%Y-%m-%d %H:%M:%S")
            cursor = db.execute(
                """
                INSERT INTO orders
                    (user_id, total, status, payment_method, customer_name, dni,
                     customer_email, phone, department, city, district, address,
                     notes, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user["id"], total, statuses[index], "Yape" if index % 2 == 0 else "Tarjeta",
                    "Cliente Demo", "76543210", demo_email, "987654321", "Lima", "Lima",
                    "San Juan de Lurigancho", "Av. Demo 123", "Pedido de demostración", date,
                ),
            )
            order_id = cursor.lastrowid
            order_number = f"TG-{order_id:06d}"
            db.execute("UPDATE orders SET order_number = ? WHERE id = ?", (order_number, order_id))
            db.execute(
                """
                INSERT INTO order_items
                    (order_id, product_id, product_name, price, quantity, color, subtotal)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (order_id, product["id"], product["name"], product["price"], quantity, "Negro", total),
            )
        db.commit()
    db.close()


def current_user() -> sqlite3.Row | None:
    user_id = session.get("user_id")
    if not user_id:
        return None
    return get_db().execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            session["next_url"] = request.path
            flash("Inicia sesión para continuar con tu compra.", "warning")
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return wrapped


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        user = current_user()
        if not user:
            session["next_url"] = request.path
            flash("Inicia sesión con una cuenta administradora.", "warning")
            return redirect(url_for("login"))
        if user["role"] != "admin":
            abort(403)
        return view(*args, **kwargs)

    return wrapped


def cart_items() -> list[dict[str, Any]]:
    raw_cart = session.get("cart", [])
    if not raw_cart:
        return []
    db = get_db()
    items: list[dict[str, Any]] = []
    for raw in raw_cart:
        product = db.execute(
            "SELECT * FROM products WHERE id = ? AND active = 1", (raw.get("product_id"),)
        ).fetchone()
        if not product:
            continue
        quantity = max(1, min(int(raw.get("quantity", 1)), int(product["stock"]) or 1))
        item = dict(product)
        item["quantity"] = quantity
        item["color"] = raw.get("color", "Negro")
        item["subtotal"] = round(float(product["price"]) * quantity, 2)
        items.append(item)
    return items


def cart_total() -> float:
    return round(sum(item["subtotal"] for item in cart_items()), 2)


@app.context_processor
def inject_layout_data() -> dict[str, Any]:
    items = cart_items()
    return {
        "current_user": current_user(),
        "cart_count": sum(item["quantity"] for item in items),
        "current_year": datetime.now().year,
    }


@app.template_filter("money")
def money(value: float | int | str) -> str:
    return f"S/ {float(value):,.2f}"


@app.route("/")
@app.route("/index.html")
def index():
    products = get_db().execute(
        "SELECT * FROM products WHERE active = 1 ORDER BY id LIMIT 6"
    ).fetchall()
    return render_template("index.html", products=products)


@app.route("/explorar")
@app.route("/explorar.html")
def explore():
    query = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()
    sort = request.args.get("sort", "featured")
    sql = "SELECT * FROM products WHERE active = 1"
    params: list[Any] = []
    if query:
        sql += " AND (name LIKE ? OR description LIKE ? OR category LIKE ?)"
        term = f"%{query}%"
        params.extend([term, term, term])
    if category:
        sql += " AND category = ?"
        params.append(category)
    order_by = {
        "price_asc": "price ASC",
        "price_desc": "price DESC",
        "stock": "stock DESC",
        "name": "name ASC",
    }.get(sort, "id ASC")
    sql += f" ORDER BY {order_by}"
    products = get_db().execute(sql, params).fetchall()
    categories = get_db().execute(
        "SELECT DISTINCT category FROM products WHERE active = 1 ORDER BY category"
    ).fetchall()
    return render_template(
        "explore.html",
        products=products,
        categories=categories,
        query=query,
        selected_category=category,
        selected_sort=sort,
    )


@app.route("/producto/<slug>")
def product_detail(slug: str):
    product = get_db().execute(
        "SELECT * FROM products WHERE slug = ? AND active = 1", (slug,)
    ).fetchone()
    if not product:
        abort(404)
    related = get_db().execute(
        "SELECT * FROM products WHERE active = 1 AND id != ? ORDER BY RANDOM() LIMIT 3",
        (product["id"],),
    ).fetchall()
    return render_template("product_detail.html", product=product, related=related)


LEGACY_PRODUCT_ROUTES = {
    "mouse-rgb.html": "mouse-rgb",
    "mouse-inalambrico.html": "mouse-inalambrico",
    "mouse-prox.html": "mouse-pro-x",
    "mouse.html": "mouse-rgb",
    "teclado.html": "teclado-tkl",
    "auriculares.html": "auriculares-7-1",
    "monitor.html": "monitor-144hz",
}


@app.route("/<path:legacy_name>")
def legacy_pages(legacy_name: str):
    if legacy_name in LEGACY_PRODUCT_ROUTES:
        return redirect(url_for("product_detail", slug=LEGACY_PRODUCT_ROUTES[legacy_name]))
    abort(404)


@app.post("/carrito/agregar")
def add_to_cart():
    product_id = request.form.get("product_id", type=int)
    quantity = request.form.get("quantity", 1, type=int)
    color = request.form.get("color", "Negro").strip()[:30]
    buy_now = request.form.get("buy_now") == "1"
    product = get_db().execute(
        "SELECT * FROM products WHERE id = ? AND active = 1", (product_id,)
    ).fetchone()
    if not product:
        abort(404)
    if product["stock"] <= 0:
        flash("Este producto no tiene stock disponible.", "error")
        return redirect(request.referrer or url_for("explore"))

    quantity = max(1, min(quantity, int(product["stock"])))
    cart = session.get("cart", [])
    existing = next(
        (
            item
            for item in cart
            if item.get("product_id") == product_id and item.get("color") == color
        ),
        None,
    )
    if existing:
        existing["quantity"] = min(int(existing.get("quantity", 1)) + quantity, int(product["stock"]))
    else:
        cart.append({"product_id": product_id, "quantity": quantity, "color": color})
    session["cart"] = cart
    session.modified = True
    flash(f"{product['name']} fue agregado al carrito.", "success")
    return redirect(url_for("checkout") if buy_now else request.referrer or url_for("cart"))


@app.route("/carrito")
@app.route("/carrito.html")
def cart():
    items = cart_items()
    return render_template("cart.html", items=items, total=cart_total())


@app.post("/carrito/actualizar")
def update_cart():
    product_id = request.form.get("product_id", type=int)
    color = request.form.get("color", "Negro")
    quantity = max(0, request.form.get("quantity", 1, type=int))
    cart_data = session.get("cart", [])
    for item in cart_data:
        if item.get("product_id") == product_id and item.get("color") == color:
            if quantity == 0:
                cart_data.remove(item)
            else:
                item["quantity"] = quantity
            break
    session["cart"] = cart_data
    session.modified = True
    flash("Carrito actualizado.", "success")
    return redirect(url_for("cart"))


@app.post("/carrito/eliminar")
def remove_from_cart():
    product_id = request.form.get("product_id", type=int)
    color = request.form.get("color", "Negro")
    session["cart"] = [
        item
        for item in session.get("cart", [])
        if not (item.get("product_id") == product_id and item.get("color") == color)
    ]
    session.modified = True
    flash("Producto eliminado del carrito.", "success")
    return redirect(url_for("cart"))


@app.post("/carrito/vaciar")
def clear_cart():
    session["cart"] = []
    session.modified = True
    flash("El carrito quedó vacío.", "success")
    return redirect(url_for("cart"))


@app.route("/checkout", methods=["GET", "POST"])
@login_required
def checkout():
    items = cart_items()
    if not items:
        flash("Agrega al menos un producto antes de continuar.", "warning")
        return redirect(url_for("explore"))
    user = current_user()
    total = cart_total()

    if request.method == "POST":
        required_fields = [
            "customer_name", "dni", "customer_email", "phone", "department",
            "city", "district", "address", "payment_method",
        ]
        missing = [field for field in required_fields if not request.form.get(field, "").strip()]
        if missing:
            flash("Completa todos los datos obligatorios de entrega.", "error")
            return render_template("checkout.html", items=items, total=total, user=user)

        db = get_db()
        try:
            for item in items:
                latest = db.execute("SELECT stock FROM products WHERE id = ?", (item["id"],)).fetchone()
                if not latest or latest["stock"] < item["quantity"]:
                    raise ValueError(f"Stock insuficiente para {item['name']}.")

            cursor = db.execute(
                """
                INSERT INTO orders
                    (user_id, total, payment_method, customer_name, dni,
                     customer_email, phone, department, city, district, address, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user["id"], total, request.form["payment_method"].strip(),
                    request.form["customer_name"].strip(), request.form["dni"].strip(),
                    request.form["customer_email"].strip().lower(), request.form["phone"].strip(),
                    request.form["department"].strip(), request.form["city"].strip(),
                    request.form["district"].strip(), request.form["address"].strip(),
                    request.form.get("notes", "").strip(),
                ),
            )
            order_id = cursor.lastrowid
            order_number = f"TG-{order_id:06d}"
            db.execute("UPDATE orders SET order_number = ? WHERE id = ?", (order_number, order_id))

            for item in items:
                db.execute(
                    """
                    INSERT INTO order_items
                        (order_id, product_id, product_name, price, quantity, color, subtotal)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        order_id, item["id"], item["name"], item["price"], item["quantity"],
                        item["color"], item["subtotal"],
                    ),
                )
                db.execute(
                    "UPDATE products SET stock = stock - ? WHERE id = ?",
                    (item["quantity"], item["id"]),
                )
            db.commit()
        except (sqlite3.DatabaseError, ValueError) as error:
            db.rollback()
            flash(str(error), "error")
            return render_template("checkout.html", items=items, total=total, user=user)

        session["cart"] = []
        session.modified = True
        flash(f"Compra {order_number} registrada correctamente.", "success")
        return redirect(url_for("receipt", order_id=order_id))

    return render_template("checkout.html", items=items, total=total, user=user)


LEGACY_CHECKOUT_ROUTES = {
    "compra-rgb.html": "mouse-rgb",
    "compra-inalambrica.html": "mouse-inalambrico",
    "compra-prox.html": "mouse-pro-x",
}


@app.route("/compra-rgb.html")
@app.route("/compra-inalambrica.html")
@app.route("/compra-prox.html")
def legacy_checkout():
    slug = LEGACY_CHECKOUT_ROUTES[request.path.lstrip("/")]
    product = get_db().execute("SELECT * FROM products WHERE slug = ?", (slug,)).fetchone()
    cart = session.get("cart", [])
    if not any(item.get("product_id") == product["id"] for item in cart):
        cart.append({"product_id": product["id"], "quantity": 1, "color": "Negro"})
        session["cart"] = cart
        session.modified = True
    return redirect(url_for("checkout"))


@app.route("/registro", methods=["GET", "POST"])
@app.route("/registro.html", methods=["GET", "POST"])
def register():
    if current_user():
        return redirect(url_for("index"))
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        if len(name) < 3:
            flash("Ingresa un nombre válido.", "error")
        elif "@" not in email:
            flash("Ingresa un correo válido.", "error")
        elif len(password) < 8:
            flash("La contraseña debe tener al menos 8 caracteres.", "error")
        elif password != confirm_password:
            flash("Las contraseñas no coinciden.", "error")
        else:
            try:
                cursor = get_db().execute(
                    "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                    (name, email, generate_password_hash(password)),
                )
                get_db().commit()
                session["user_id"] = cursor.lastrowid
                flash("Tu cuenta fue creada correctamente.", "success")
                return redirect(url_for("index"))
            except sqlite3.IntegrityError:
                flash("Ese correo ya está registrado.", "error")
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
@app.route("/login.html", methods=["GET", "POST"])
def login():
    if current_user():
        return redirect(url_for("index"))
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = get_db().execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        if user and check_password_hash(user["password_hash"], password):
            next_url = session.get("next_url")
            session.clear()
            session["user_id"] = user["id"]
            flash(f"Bienvenido, {user['name']}.", "success")
            return redirect(next_url or url_for("index"))
        flash("Correo o contraseña incorrectos.", "error")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Sesión cerrada correctamente.", "success")
    return redirect(url_for("index"))


@app.route("/mis-compras.html")
@app.route("/mis-compras")
@login_required
def purchases():
    orders = get_db().execute(
        "SELECT * FROM orders WHERE user_id = ? ORDER BY created_at DESC, id DESC",
        (session["user_id"],),
    ).fetchall()
    return render_template("purchases.html", orders=orders)


@app.route("/boleta/<int:order_id>")
@login_required
def receipt(order_id: int):
    user = current_user()
    order = get_db().execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
    if not order or (user["role"] != "admin" and order["user_id"] != user["id"]):
        abort(404)
    items = get_db().execute(
        "SELECT * FROM order_items WHERE order_id = ? ORDER BY id", (order_id,)
    ).fetchall()
    return render_template("receipt.html", order=order, items=items)


@app.post("/contacto")
def contact():
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    message = request.form.get("message", "").strip()
    if not name or "@" not in email or len(message) < 10:
        flash("Completa correctamente el formulario de contacto.", "error")
    else:
        get_db().execute(
            "INSERT INTO contact_messages (name, email, message) VALUES (?, ?, ?)",
            (name, email, message),
        )
        get_db().commit()
        flash("Tu mensaje fue enviado. Te responderemos pronto.", "success")
    return redirect(url_for("index") + "#contacto")


@app.route("/admin.html")
@app.route("/admin")
@admin_required
def admin_dashboard():
    db = get_db()
    metrics = {
        "users": db.execute("SELECT COUNT(*) AS value FROM users").fetchone()["value"],
        "orders": db.execute("SELECT COUNT(*) AS value FROM orders").fetchone()["value"],
        "revenue": db.execute("SELECT COALESCE(SUM(total), 0) AS value FROM orders").fetchone()["value"],
        "today": db.execute(
            "SELECT COALESCE(SUM(total), 0) AS value FROM orders WHERE DATE(created_at) = DATE('now', 'localtime')"
        ).fetchone()["value"],
        "month": db.execute(
            "SELECT COALESCE(SUM(total), 0) AS value FROM orders WHERE strftime('%Y-%m', created_at) = strftime('%Y-%m', 'now', 'localtime')"
        ).fetchone()["value"],
        "ticket": db.execute("SELECT COALESCE(AVG(total), 0) AS value FROM orders").fetchone()["value"],
        "low_stock": db.execute("SELECT COUNT(*) AS value FROM products WHERE stock <= 8").fetchone()["value"],
        "messages": db.execute("SELECT COUNT(*) AS value FROM contact_messages").fetchone()["value"],
    }
    orders = db.execute(
        """
        SELECT o.*, u.name AS user_name FROM orders o
        JOIN users u ON u.id = o.user_id
        ORDER BY o.created_at DESC, o.id DESC LIMIT 12
        """
    ).fetchall()
    users = db.execute("SELECT * FROM users ORDER BY created_at DESC LIMIT 8").fetchall()
    products = db.execute("SELECT * FROM products ORDER BY stock ASC, name").fetchall()
    messages = db.execute("SELECT * FROM contact_messages ORDER BY created_at DESC LIMIT 8").fetchall()
    top_products = db.execute(
        """
        SELECT product_name, SUM(quantity) AS units, SUM(subtotal) AS total
        FROM order_items GROUP BY product_name ORDER BY units DESC LIMIT 5
        """
    ).fetchall()
    status_counts = db.execute(
        "SELECT status, COUNT(*) AS total FROM orders GROUP BY status ORDER BY total DESC"
    ).fetchall()

    sales_rows = db.execute(
        """
        SELECT DATE(created_at) AS day, SUM(total) AS total
        FROM orders
        WHERE DATE(created_at) >= DATE('now', '-6 days')
        GROUP BY DATE(created_at)
        """
    ).fetchall()
    sales_map = {row["day"]: float(row["total"]) for row in sales_rows}
    sales_chart = []
    for days_ago in range(6, -1, -1):
        day = (datetime.now() - timedelta(days=days_ago)).date()
        sales_chart.append({"label": day.strftime("%d/%m"), "value": sales_map.get(day.isoformat(), 0)})
    max_sale = max([point["value"] for point in sales_chart] or [1]) or 1

    return render_template(
        "admin.html",
        metrics=metrics,
        orders=orders,
        users=users,
        products=products,
        messages=messages,
        top_products=top_products,
        status_counts=status_counts,
        sales_chart=sales_chart,
        max_sale=max_sale,
    )


@app.post("/admin/pedido/<int:order_id>/estado")
@admin_required
def update_order_status(order_id: int):
    allowed = {"Confirmado", "Preparando", "Enviado", "Entregado", "Cancelado"}
    status = request.form.get("status", "")
    if status not in allowed:
        abort(400)
    get_db().execute("UPDATE orders SET status = ? WHERE id = ?", (status, order_id))
    get_db().commit()
    flash("Estado del pedido actualizado.", "success")
    return redirect(url_for("admin_dashboard") + "#pedidos")


@app.post("/admin/producto/<int:product_id>/stock")
@admin_required
def update_product_stock(product_id: int):
    stock = max(0, request.form.get("stock", 0, type=int))
    get_db().execute("UPDATE products SET stock = ? WHERE id = ?", (stock, product_id))
    get_db().commit()
    flash("Stock actualizado correctamente.", "success")
    return redirect(url_for("admin_dashboard") + "#inventario")


@app.get("/api/cart-count")
def cart_count_api():
    return jsonify({"count": sum(item["quantity"] for item in cart_items())})


def render_error_page(code: int, title: str, message: str):
    error_template = BASE_DIR / "templates" / "error.html"
    if error_template.exists():
        return render_template(
            "error.html",
            code=code,
            title=title,
            message=message,
        ), code

    # Respuesta de emergencia para que un archivo faltante no provoque otro error.
    return f"""<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{code} | Tienda Gemer</title>
  <style>
    body{{font-family:Arial,sans-serif;background:#0b0d12;color:#fff;
         min-height:100vh;display:grid;place-items:center;margin:0}}
    main{{max-width:620px;padding:32px;text-align:center}}
    a{{color:#7dd3fc}}
  </style>
</head>
<body>
  <main>
    <h1>{code} - {title}</h1>
    <p>{message}</p>
    <p>Comprueba que la carpeta <strong>templates</strong> esté en la raíz del proyecto.</p>
    <a href="/">Volver al inicio</a>
  </main>
</body>
</html>""", code


@app.errorhandler(403)
def forbidden(_: Exception):
    return render_error_page(
        403,
        "Acceso restringido",
        "No tienes permisos para entrar a esta sección.",
    )


@app.errorhandler(404)
def not_found(_: Exception):
    return render_error_page(
        404,
        "Página no encontrada",
        "La dirección solicitada no existe o fue movida.",
    )


@app.errorhandler(500)
def server_error(_: Exception):
    return render_error_page(
        500,
        "Error interno",
        "Ocurrió un problema inesperado. Intenta nuevamente.",
    )


init_db()

if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    debug_mode = os.getenv("FLASK_DEBUG") == "1"

    # Al ejecutar localmente, abre la tienda en el navegador automáticamente.
    # En Render se usa Gunicorn, por lo que este bloque no se ejecuta.
    if os.getenv("NO_BROWSER") != "1" and not debug_mode:
        threading.Timer(1.4, lambda: webbrowser.open(f"http://127.0.0.1:{port}")).start()

    app.run(host="0.0.0.0", port=port, debug=debug_mode, use_reloader=debug_mode)
