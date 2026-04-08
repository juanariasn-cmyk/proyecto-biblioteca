from flask import Flask, render_template, request, redirect, session, Response
import sqlite3, os, csv
from datetime import datetime

app = Flask(__name__)
app.secret_key = "empresa123"

UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

def db():
    return sqlite3.connect("db.db")

# ================= DB =================
def init_db():
    conn = db()
    cur = conn.cursor()

    cur.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user TEXT, pass TEXT, rol TEXT)""")

    cur.execute("""CREATE TABLE IF NOT EXISTS libros (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        titulo TEXT, autor TEXT,
        imagen TEXT, disponible INTEGER)""")

    cur.execute("""CREATE TABLE IF NOT EXISTS prestamos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user TEXT, libro_id INTEGER,
        fecha TEXT, devuelto INTEGER DEFAULT 0)""")

    conn.commit()
    conn.close()

init_db()

# ================= LOGIN =================
@app.route("/", methods=["GET","POST"])
def login():
    error = None
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
@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        u = request.form["user"]
        p = request.form["password"]

        conn = db()
        cur = conn.cursor()
        cur.execute("INSERT INTO users VALUES (NULL,?,?, 'user')", (u,p))
        conn.commit()
        conn.close()

        return redirect("/")

    return render_template("register.html")

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
    SELECT prestamos.id, libros.titulo, prestamos.fecha, prestamos.devuelto,
    julianday('now') - julianday(prestamos.fecha)
    FROM prestamos
    JOIN libros ON libros.id = prestamos.libro_id
    WHERE prestamos.user=?
    """, (session["user"],))

    prestamos = cur.fetchall()
    conn.close()

    return render_template("dashboard.html", libros=libros, prestamos=prestamos)

# ================= ADMIN =================
@app.route("/admin")
def admin():
    if session.get("rol") != "admin":
        return redirect("/")

    conn = db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM libros")
    libros = cur.fetchall()

    cur.execute("SELECT * FROM users")
    users = cur.fetchall()

    cur.execute("""
    SELECT prestamos.id, users.user, libros.titulo, prestamos.fecha,
    prestamos.devuelto,
    julianday('now') - julianday(prestamos.fecha)
    FROM prestamos
    JOIN libros ON libros.id = prestamos.libro_id
    JOIN users ON users.user = prestamos.user
    """)
    prestamos = cur.fetchall()

    conn.close()

    return render_template("admin.html",
        libros=libros, users=users, prestamos=prestamos)

# ================= ADD =================
@app.route("/add_book", methods=["POST"])
def add_book():
    titulo = request.form["titulo"]
    autor = request.form["autor"]
    file = request.files["imagen"]

    filename = file.filename
    file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

    conn = db()
    cur = conn.cursor()
    cur.execute("INSERT INTO libros VALUES (NULL,?,?,?,1)", (titulo, autor, filename))
    conn.commit()
    conn.close()

    return redirect("/admin")

# ================= PRESTAR =================
@app.route("/prestar/<int:id>")
def prestar(id):
    conn = db()
    cur = conn.cursor()

    cur.execute("UPDATE libros SET disponible=0 WHERE id=?", (id,))
    cur.execute("INSERT INTO prestamos VALUES (NULL,?,?,?,0)",
                (session["user"], id, datetime.now().strftime("%Y-%m-%d")))

    conn.commit()
    conn.close()
    return redirect("/dashboard")

# ================= DEVOLVER =================
@app.route("/devolver/<int:id>")
def devolver(id):
    conn = db()
    cur = conn.cursor()

    cur.execute("UPDATE prestamos SET devuelto=1 WHERE id=?", (id,))
    cur.execute("UPDATE libros SET disponible=1 WHERE id=(SELECT libro_id FROM prestamos WHERE id=?)", (id,))

    conn.commit()
    conn.close()
    return redirect("/dashboard")

# ================= EXPORT CSV =================
@app.route("/export")
def export():
    conn = db()
    cur = conn.cursor()

    cur.execute("""
    SELECT users.user, libros.titulo, prestamos.fecha, prestamos.devuelto
    FROM prestamos
    JOIN libros ON libros.id = prestamos.libro_id
    JOIN users ON users.user = prestamos.user
    """)

    data = cur.fetchall()

    def generate():
        yield "Usuario,Libro,Fecha,Estado\n"
        for row in data:
            estado = "Devuelto" if row[3] else "Prestado"
            yield f"{row[0]},{row[1]},{row[2]},{estado}\n"

    return Response(generate(), mimetype="text/csv",
                    headers={"Content-Disposition":"attachment;filename=reporte.csv"})

# ================= API =================
@app.route("/api/libros")
def api_libros():
    conn = db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM libros")
    libros = cur.fetchall()

    lista = []
    for l in libros:
        lista.append({
            "id": l[0],
            "titulo": l[1],
            "autor": l[2],
            "imagen": l[3],
            "disponible": l[4]
        })

    return {"libros": lista}

# ================= LOGOUT =================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
