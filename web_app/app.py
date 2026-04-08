from flask import Flask, render_template, request, redirect, session, flash
import sqlite3, os
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = "secret123"

def db():
    return sqlite3.connect("db.db", check_same_thread=False)

def init_db():
    conn = db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user TEXT UNIQUE,
        pass TEXT,
        rol TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS books (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT,
        autor TEXT,
        imagen TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS prestamos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        libro_id INTEGER,
        usuario TEXT,
        fecha TEXT,
        devolucion TEXT,
        devuelto INTEGER DEFAULT 0
    )
    """)

    # admin
    cur.execute("SELECT * FROM users WHERE user='admin'")
    if not cur.fetchone():
        cur.execute(
            "INSERT INTO users (user, pass, rol) VALUES (?,?,?)",
            ("admin", generate_password_hash("1234"), "admin")
        )

    conn.commit()
    conn.close()

init_db()

# LOGIN
@app.route("/", methods=["GET","POST"])
def login():
    if request.method == "POST":
        u = request.form["user"]
        p = request.form["password"]

        conn = db()
        cur = conn.cursor()
        cur.execute("SELECT pass, rol FROM users WHERE user=?", (u,))
        user = cur.fetchone()

        if user and check_password_hash(user[0], p):
            session["user"] = u
            session["rol"] = user[1]
            return redirect("/dashboard")
        else:
            flash("❌ Usuario o contraseña incorrectos")

    return render_template("login.html")

# REGISTER
@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        u = request.form["user"]
        p = generate_password_hash(request.form["password"])

        conn = db()
        cur = conn.cursor()
        try:
            cur.execute(
                "INSERT INTO users (user, pass, rol) VALUES (?,?,?)",
                (u, p, "user")
            )
            conn.commit()
            flash("Usuario creado")
            return redirect("/")
        except:
            flash("Usuario ya existe")

    return render_template("register.html")

# DASHBOARD
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/")

    conn = db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM books")
    libros = cur.fetchall()

    cur.execute("SELECT libro_id FROM prestamos WHERE devuelto=0")
    prestados = [x[0] for x in cur.fetchall()]

    cur.execute("""
    SELECT COUNT(*) FROM prestamos 
    WHERE devolucion < date('now') AND devuelto=0
    """)
    atrasados = cur.fetchone()[0]

    return render_template("dashboard.html",
        libros=libros,
        prestados=prestados,
        atrasados=atrasados,
        rol=session.get("rol")
    )

# AGREGAR LIBRO
@app.route("/add", methods=["POST"])
def add():
    if session.get("rol") != "admin":
        flash("❌ Solo admin")
        return redirect("/dashboard")

    nombre = request.form["nombre"]
    autor = request.form["autor"]
    imagen = request.form["imagen"]

    conn = db()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO books (nombre, autor, imagen) VALUES (?,?,?)",
        (nombre, autor, imagen)
    )
    conn.commit()

    flash("Libro agregado")
    return redirect("/dashboard")

# PRESTAR
@app.route("/prestar/<int:id>")
def prestar(id):
    conn = db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM prestamos WHERE libro_id=? AND devuelto=0", (id,))
    if cur.fetchone():
        flash("Libro no disponible")
        return redirect("/dashboard")

    hoy = datetime.now()
    devolucion = hoy + timedelta(days=7)

    cur.execute("""
    INSERT INTO prestamos (libro_id, usuario, fecha, devolucion)
    VALUES (?,?,?,?)
    """, (id, session["user"], hoy.strftime("%Y-%m-%d"), devolucion.strftime("%Y-%m-%d")))

    conn.commit()
    flash("Libro prestado")
    return redirect("/dashboard")

# DEVOLVER
@app.route("/devolver/<int:id>")
def devolver(id):
    conn = db()
    cur = conn.cursor()

    cur.execute("UPDATE prestamos SET devuelto=1 WHERE libro_id=? AND devuelto=0", (id,))
    conn.commit()

    flash("Libro devuelto")
    return redirect("/dashboard")

# ADMIN
@app.route("/admin")
def admin():
    if session.get("rol") != "admin":
        return redirect("/dashboard")

    conn = db()
    cur = conn.cursor()

    cur.execute("""
    SELECT prestamos.id, books.nombre, prestamos.usuario, prestamos.devuelto
    FROM prestamos
    JOIN books ON prestamos.libro_id = books.id
    """)
    datos = cur.fetchall()

    return render_template("admin.html", datos=datos)

# TEMA
@app.route("/tema/<modo>")
def tema(modo):
    session["tema"] = modo
    return redirect("/dashboard")

# LOGOUT
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
