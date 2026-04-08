from flask import Flask, render_template, request, redirect, session
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "final123"

# ================= DB =================
def db():
    return sqlite3.connect("db.db")

def init_db():
    conn = db()
    cur = conn.cursor()

    cur.execute("""CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user TEXT,
        pass TEXT,
        rol TEXT)""")

    cur.execute("""CREATE TABLE IF NOT EXISTS libros(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        titulo TEXT,
        autor TEXT,
        imagen TEXT,
        disponible INTEGER DEFAULT 1)""")

    cur.execute("""CREATE TABLE IF NOT EXISTS prestamos(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario TEXT,
        libro_id INTEGER,
        fecha TEXT)""")

    # ADMIN POR DEFECTO
    cur.execute("SELECT * FROM users WHERE user='admin'")
    if not cur.fetchone():
        cur.execute("INSERT INTO users (user, pass, rol) VALUES ('admin','1234','admin')")

    conn.commit()
    conn.close()

init_db()

# ================= LOGIN =================
@app.route("/", methods=["GET","POST"])
def login():
    error = None

    # 🔥 FORZAR LOGIN SIEMPRE
    if "user" in session:
        session.clear()

    if request.method == "POST":
        u = request.form["user"]
        p = request.form["password"]

        conn = db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE user=? AND pass=?", (u,p))
        user = cur.fetchone()
        conn.close()

        if user:
            session["user"] = user[1]
            session["rol"] = user[3]

            return redirect("/admin" if user[3]=="admin" else "/dashboard")
        else:
            error = "❌ Usuario o contraseña incorrectos"

    return render_template("login.html", error=error)

# ================= REGISTER =================
@app.route("/register", methods=["POST"])
def register():
    u = request.form["user"]
    p = request.form["password"]

    conn = db()
    cur = conn.cursor()
    cur.execute("INSERT INTO users (user, pass, rol) VALUES (?,?,'user')", (u,p))
    conn.commit()
    conn.close()

    return redirect("/")

# ================= DASHBOARD =================
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/")

    conn = db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM libros")
    libros = cur.fetchall()

    cur.execute("""
        SELECT prestamos.libro_id, libros.titulo, prestamos.fecha
        FROM prestamos
        JOIN libros ON libros.id = prestamos.libro_id
        WHERE prestamos.usuario=?
    """, (session["user"],))

    prestamos = cur.fetchall()

    conn.close()

    return render_template("dashboard.html", libros=libros, prestamos=prestamos)

# ================= ADMIN =================
@app.route("/admin")
def admin():
    if "user" not in session or session["rol"] != "admin":
        return redirect("/")

    conn = db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM libros")
    libros = cur.fetchall()

    cur.execute("SELECT * FROM users")
    users = cur.fetchall()

    cur.execute("""
        SELECT prestamos.id, prestamos.usuario, libros.titulo, prestamos.fecha
        FROM prestamos
        JOIN libros ON libros.id = prestamos.libro_id
    """)
    prestamos = cur.fetchall()

    conn.close()

    return render_template("admin.html", libros=libros, users=users, prestamos=prestamos)

# ================= ADD BOOK =================
@app.route("/add_book", methods=["POST"])
def add_book():
    titulo = request.form["titulo"]
    autor = request.form["autor"]
    imagen = request.form["imagen"]

    conn = db()
    cur = conn.cursor()
    cur.execute("INSERT INTO libros (titulo, autor, imagen) VALUES (?,?,?)",
                (titulo, autor, imagen))
    conn.commit()
    conn.close()

    return redirect("/admin")

# ================= PRESTAR =================
@app.route("/prestar/<int:id>", methods=["POST"])
def prestar(id):
    if "user" not in session:
        return redirect("/")

    conn = db()
    cur = conn.cursor()

    cur.execute("SELECT disponible FROM libros WHERE id=?", (id,))
    libro = cur.fetchone()

    if libro and libro[0] == 1:
        fecha = datetime.now().strftime("%Y-%m-%d")

        cur.execute("INSERT INTO prestamos (usuario, libro_id, fecha) VALUES (?,?,?)",
                    (session["user"], id, fecha))

        cur.execute("UPDATE libros SET disponible=0 WHERE id=?", (id,))
        conn.commit()

    conn.close()
    return redirect("/dashboard")

# ================= DEVOLVER =================
@app.route("/devolver/<int:id>")
def devolver(id):
    conn = db()
    cur = conn.cursor()

    cur.execute("DELETE FROM prestamos WHERE libro_id=? AND usuario=?",
                (id, session["user"]))

    cur.execute("UPDATE libros SET disponible=1 WHERE id=?", (id,))
    conn.commit()
    conn.close()

    return redirect("/dashboard")

# ================= LOGOUT =================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ================= RUN =================
if __name__ == "__main__":
    app.run(debug=True)
