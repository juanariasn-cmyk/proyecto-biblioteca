from flask import Flask, render_template, request, redirect, session, flash
import sqlite3
import os
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
        pass TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS books (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT,
        autor TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()

# 🔐 LOGIN
@app.route("/", methods=["GET","POST"])
def login():
    if request.method == "POST":
        u = request.form["user"]
        p = request.form["password"]

        conn = db()
        cur = conn.cursor()
        cur.execute("SELECT pass FROM users WHERE user=?", (u,))
        user = cur.fetchone()

        if user and check_password_hash(user[0], p):
            session["user"] = u
            return redirect("/dashboard")
        else:
            flash("Credenciales incorrectas")

    return render_template("login.html")


# 🧾 REGISTRO
@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        u = request.form["user"]
        p = generate_password_hash(request.form["password"])

        conn = db()
        cur = conn.cursor()

        try:
            cur.execute("INSERT INTO users (user, pass) VALUES (?,?)", (u,p))
            conn.commit()
            flash("Usuario creado")
            return redirect("/")
        except:
            flash("Usuario ya existe")

    return render_template("register.html")


# 📊 DASHBOARD
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
                           total_libros=total_libros)


# ➕ AGREGAR LIBRO
@app.route("/add", methods=["POST"])
def add():
    nombre = request.form["nombre"]
    autor = request.form["autor"]

    conn = db()
    cur = conn.cursor()
    cur.execute("INSERT INTO books (nombre, autor) VALUES (?,?)", (nombre, autor))
    conn.commit()

    flash("Libro agregado")
    return redirect("/dashboard")


# ❌ ELIMINAR
@app.route("/delete/<int:id>")
def delete(id):
    conn = db()
    cur = conn.cursor()
    cur.execute("DELETE FROM books WHERE id=?", (id,))
    conn.commit()

    flash("Libro eliminado")
    return redirect("/dashboard")


# 🚪 LOGOUT
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# 🔥 CONFIG RENDER
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
