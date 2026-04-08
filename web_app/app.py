from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "super_secret_key_123"

# ======================
# BASE DE DATOS
# ======================
def db():
    return sqlite3.connect("db.db")

# ======================
# CREAR TABLAS
# ======================
def init_db():
    conn = db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user TEXT UNIQUE,
        pass TEXT,
        role TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS libros (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        titulo TEXT,
        autor TEXT,
        imagen TEXT,
        disponible INTEGER DEFAULT 1
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS prestamos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user TEXT,
        libro_id INTEGER
    )
    """)

    # CREAR ADMIN SI NO EXISTE
    cur.execute("SELECT * FROM users WHERE user='admin'")
    if not cur.fetchone():
        cur.execute("INSERT INTO users (user, pass, role) VALUES (?, ?, ?)", 
                    ("admin", "admin", "admin"))

    conn.commit()
    conn.close()

init_db()

# ======================
# LOGIN
# ======================
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        u = request.form["user"]
        p = request.form["password"]

        conn = db()
        cur = conn.cursor()

        cur.execute("SELECT user, role FROM users WHERE user=? AND pass=?", (u, p))
        user = cur.fetchone()

        if user:
            session["user"] = user[0]
            session["role"] = user[1]

            if user[1] == "admin":
                return redirect("/admin")
            else:
                return redirect("/usuario")
        else:
            return render_template("login.html", error="Usuario o contraseña incorrectos")

    return render_template("login.html")


# ======================
# REGISTRO
# ======================
@app.route("/register", methods=["POST"])
def register():
    u = request.form["user"]
    p = request.form["password"]

    conn = db()
    cur = conn.cursor()

    try:
        cur.execute("INSERT INTO users (user, pass, role) VALUES (?, ?, ?)", 
                    (u, p, "user"))
        conn.commit()
    except:
        return "Usuario ya existe"

    return redirect("/")


# ======================
# USUARIO
# ======================
@app.route("/usuario")
def usuario():
    if "user" not in session:
        return redirect("/")

    conn = db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM libros WHERE disponible=1")
    libros = cur.fetchall()

    cur.execute("""
        SELECT libros.titulo, libros.imagen 
        FROM prestamos 
        JOIN libros ON prestamos.libro_id = libros.id
        WHERE prestamos.user=?
    """, (session["user"],))
    prestamos = cur.fetchall()

    return render_template("usuario.html", 
                           user=session["user"], 
                           libros=libros, 
                           prestamos=prestamos)


# ======================
# PEDIR LIBRO
# ======================
@app.route("/prestar/<int:id>")
def prestar(id):
    if "user" not in session:
        return redirect("/")

    conn = db()
    cur = conn.cursor()

    # verificar si ya está prestado
    cur.execute("SELECT disponible FROM libros WHERE id=?", (id,))
    disponible = cur.fetchone()

    if disponible and disponible[0] == 1:
        cur.execute("INSERT INTO prestamos (user, libro_id) VALUES (?, ?)", 
                    (session["user"], id))
        cur.execute("UPDATE libros SET disponible=0 WHERE id=?", (id,))
        conn.commit()

    return redirect("/usuario")


# ======================
# ADMIN
# ======================
@app.route("/admin")
def admin():
    if "user" not in session or session["role"] != "admin":
        return redirect("/")

    conn = db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM libros")
    libros = cur.fetchall()

    cur.execute("SELECT * FROM users")
    users = cur.fetchall()

    cur.execute("""
        SELECT prestamos.user, libros.titulo 
        FROM prestamos 
        JOIN libros ON prestamos.libro_id = libros.id
    """)
    prestamos = cur.fetchall()

    return render_template("admin.html", 
                           libros=libros, 
                           users=users, 
                           prestamos=prestamos)


# ======================
# AGREGAR LIBRO
# ======================
@app.route("/add_libro", methods=["POST"])
def add_libro():
    if session.get("role") != "admin":
        return redirect("/")

    titulo = request.form["titulo"]
    autor = request.form["autor"]
    imagen = request.form["imagen"]

    conn = db()
    cur = conn.cursor()

    cur.execute("INSERT INTO libros (titulo, autor, imagen) VALUES (?, ?, ?)", 
                (titulo, autor, imagen))
    conn.commit()

    return redirect("/admin")


# ======================
# LOGOUT
# ======================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# ======================
# RUN
# ======================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
