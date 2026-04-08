from flask import Flask, render_template, request, redirect, session, flash
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "secret123"

def db():
    return sqlite3.connect("db.db", check_same_thread=False)

def init_db():
    conn = db()
    cur = conn.cursor()

    cur.execute("CREATE TABLE IF NOT EXISTS users (user TEXT, pass TEXT)")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT,
            autor TEXT
        )
    """)

    # usuario default
    cur.execute("SELECT * FROM users WHERE user='admin'")
    if not cur.fetchone():
        cur.execute("INSERT INTO users VALUES ('admin', '1234')")

    conn.commit()
    conn.close()

init_db()

@app.route("/", methods=["GET","POST"])
def login():
    if request.method == "POST":
        u = request.form["user"]
        p = request.form["password"]
        conn = db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE user=? AND pass=?", (u,p))
        if cur.fetchone():
            session["user"] = u
            return redirect("/dashboard")
        else:
            flash("Credenciales incorrectas")
    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/")

    conn = db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM books")
    libros = cur.fetchall()

    cur.execute("SELECT COUNT(*) FROM books")
    total = cur.fetchone()[0]

    return render_template("dashboard.html", libros=libros, total=total)

@app.route("/add", methods=["POST"])
def add():
    nombre = request.form["nombre"]
    autor = request.form["autor"]

    conn = db()
    cur = conn.cursor()
    cur.execute("INSERT INTO books (nombre, autor) VALUES (?,?)", (nombre, autor))
    conn.commit()

    flash("Libro agregado correctamente")
    return redirect("/dashboard")

@app.route("/delete/<int:id>")
def delete(id):
    conn = db()
    cur = conn.cursor()
    cur.execute("DELETE FROM books WHERE id=?", (id,))
    conn.commit()

    flash("Libro eliminado")
    return redirect("/dashboard")

@app.route("/search", methods=["POST"])
def search():
    query = request.form["query"]

    conn = db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM books WHERE nombre LIKE ?", ('%'+query+'%',))
    libros = cur.fetchall()

    return render_template("dashboard.html", libros=libros, total=len(libros))

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
