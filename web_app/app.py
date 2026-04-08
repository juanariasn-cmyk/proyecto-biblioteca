from flask import Flask, render_template, request, redirect, session, flash
import sqlite3, os
from werkzeug.security import generate_password_hash, check_password_hash

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
        autor TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS prestamos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        libro_id INTEGER,
        usuario TEXT
    )
    """)

    # admin por defecto
    cur.execute("SELECT * FROM users WHERE user='admin'")
    if not cur.fetchone():
        cur.execute("INSERT INTO users (user, pass, rol) VALUES (?,?,?)",
                    ("admin", generate_password_hash("1234"), "admin"))

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
            flash("Credenciales incorrectas")

    return render_template("login.html")

# REGISTRO (usuarios normales)
@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        u = request.form["user"]
        p = generate_password_hash(request.form["password"])

        conn = db()
        cur = conn.cursor()
        try:
            cur.execute("INSERT INTO users (user, pass, rol) VALUES (?,?,?)",
                        (u,p,"user"))
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

    cur.execute("SELECT COUNT(*) FROM books")
    total_libros = cur.fetchone()[0]

    return render_template("dashboard.html",
                           libros=libros,
                           total_libros=total_libros,
                           rol=session["rol"])

# PRESTAR
@app.route("/prestar/<int:id>")
def prestar(id):
    user = session["user"]

    conn = db()
    cur = conn.cursor()
    cur.execute("INSERT INTO prestamos (libro_id, usuario) VALUES (?,?)",
                (id,user))
    conn.commit()

    flash("Libro prestado")
    return redirect("/dashboard")

# PANEL ADMIN
@app.route("/admin")
def admin():
    if session.get("rol") != "admin":
        return redirect("/dashboard")

    conn = db()
    cur = conn.cursor()

    cur.execute("""
    SELECT prestamos.id, books.nombre, prestamos.usuario
    FROM prestamos
    JOIN books ON prestamos.libro_id = books.id
    """)
    datos = cur.fetchall()

    return render_template("admin.html", datos=datos)

# AGREGAR LIBRO
@app.route("/add", methods=["POST"])
def add():
    if session.get("rol") != "admin":
        return redirect("/dashboard")

    nombre = request.form["nombre"]
    autor = request.form["autor"]

    conn = db()
    cur = conn.cursor()
    cur.execute("INSERT INTO books (nombre, autor) VALUES (?,?)", (nombre, autor))
    conn.commit()

    return redirect("/dashboard")

# LOGOUT
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
