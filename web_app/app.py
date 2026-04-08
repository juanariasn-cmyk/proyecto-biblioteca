from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = "ultra_pro_key"

# =========================
# DB
# =========================
def db():
    return sqlite3.connect('db.db')

def crear_db():
    conn = db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario TEXT UNIQUE,
        password TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS libros(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        titulo TEXT,
        autor TEXT,
        imagen TEXT,
        disponible INTEGER
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS prestamos(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario TEXT,
        libro_id INTEGER,
        fecha TEXT,
        devuelto INTEGER
    )
    """)

    # ADMIN AUTO
    cur.execute("SELECT * FROM users WHERE usuario='admin'")
    if not cur.fetchone():
        cur.execute("INSERT INTO users(usuario,password) VALUES('admin','123')")

    conn.commit()
    conn.close()

crear_db()

# =========================
# LOGIN
# =========================
@app.route('/', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        u = request.form.get('usuario')
        p = request.form.get('password')

        conn = db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE usuario=? AND password=?", (u,p))
        user = cur.fetchone()
        conn.close()

        if user:
            session['user'] = u
            return redirect('/admin' if u == 'admin' else '/usuario')

        return render_template('login.html', error="❌ Usuario o contraseña incorrectos")

    return render_template('login.html')

# =========================
# REGISTRO (ARREGLADO 🔥)
# =========================
@app.route('/registro', methods=['GET','POST'])
def registro():
    if request.method == 'POST':
        u = request.form.get('usuario')
        p = request.form.get('password')

        if not u or not p:
            return render_template('registro.html', error="Completa todos los campos")

        conn = db()
        cur = conn.cursor()

        try:
            cur.execute("INSERT INTO users(usuario,password) VALUES(?,?)", (u,p))
            conn.commit()
            conn.close()
            return redirect('/')
        except sqlite3.IntegrityError:
            conn.close()
            return render_template('registro.html', error="❌ Usuario ya existe")
        except Exception as e:
            conn.close()
            return render_template('registro.html', error="Error inesperado")

    return render_template('registro.html')

# =========================
# USUARIO
# =========================
@app.route('/usuario')
def usuario():
    if 'user' not in session:
        return redirect('/')

    conn = db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM libros")
    libros = cur.fetchall()

    cur.execute("""
    SELECT prestamos.id, libros.titulo, prestamos.fecha, prestamos.devuelto
    FROM prestamos
    JOIN libros ON libros.id = prestamos.libro_id
    WHERE prestamos.usuario=?
    """, (session['user'],))

    prestamos = cur.fetchall()

    conn.close()

    return render_template('usuario.html', libros=libros, prestamos=prestamos)

# =========================
# ADMIN
# =========================
@app.route('/admin', methods=['GET','POST'])
def admin():
    if 'user' not in session or session['user'] != 'admin':
        return redirect('/')

    conn = db()
    cur = conn.cursor()

    if request.method == 'POST':
        titulo = request.form.get('titulo')
        autor = request.form.get('autor')

        if titulo and autor:
            cur.execute("INSERT INTO libros(titulo,autor,imagen,disponible) VALUES(?,?,?,1)",
                        (titulo, autor, 'default.png'))
            conn.commit()

    cur.execute("SELECT * FROM libros")
    libros = cur.fetchall()

    conn.close()

    return render_template('admin.html', libros=libros)

# =========================
# PRESTAR
# =========================
@app.route('/prestar/<int:id>', methods=['POST'])
def prestar(id):
    conn = db()
    cur = conn.cursor()

    cur.execute("UPDATE libros SET disponible=0 WHERE id=?", (id,))
    cur.execute("INSERT INTO prestamos(usuario,libro_id,fecha,devuelto) VALUES(?,?,date('now'),0)",
                (session['user'], id))

    conn.commit()
    conn.close()

    return redirect('/usuario')

# =========================
# DEVOLVER
# =========================
@app.route('/devolver/<int:id>', methods=['POST'])
def devolver(id):
    conn = db()
    cur = conn.cursor()

    cur.execute("UPDATE prestamos SET devuelto=1 WHERE id=?", (id,))
    cur.execute("UPDATE libros SET disponible=1 WHERE id=(SELECT libro_id FROM prestamos WHERE id=?)", (id,))

    conn.commit()
    conn.close()

    return redirect('/usuario')

# =========================
# LOGOUT
# =========================
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
