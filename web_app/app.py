from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = "clave_super_segura"

# =========================
# CREAR BASE DE DATOS
# =========================
def crear_db():
    conn = sqlite3.connect('db.db')
    cur = conn.cursor()

    # TABLA USUARIOS
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario TEXT UNIQUE,
        password TEXT
    )
    """)

    # TABLA LIBROS
    cur.execute("""
    CREATE TABLE IF NOT EXISTS libros (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        titulo TEXT,
        autor TEXT,
        imagen TEXT,
        disponible INTEGER
    )
    """)

    # TABLA PRESTAMOS
    cur.execute("""
    CREATE TABLE IF NOT EXISTS prestamos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario TEXT,
        libro_id INTEGER,
        fecha TEXT,
        devuelto INTEGER
    )
    """)

    # CREAR ADMIN SI NO EXISTE
    cur.execute("SELECT * FROM users WHERE usuario='admin'")
    if not cur.fetchone():
        cur.execute("INSERT INTO users (usuario, password) VALUES (?, ?)", ("admin", "123"))

    conn.commit()
    conn.close()

crear_db()

# =========================
# LOGIN
# =========================
@app.route('/', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        usuario = request.form['usuario']
        password = request.form['password']

        conn = sqlite3.connect('db.db')
        cur = conn.cursor()

        cur.execute("SELECT * FROM users WHERE usuario=? AND password=?", (usuario, password))
        user = cur.fetchone()

        conn.close()

        if user:
            session['user'] = usuario
            return redirect('/usuario')
        else:
            return render_template('login.html', error="❌ Datos incorrectos")

    return render_template('login.html')

# =========================
# REGISTRO
# =========================
@app.route('/registro', methods=['GET','POST'])
def registro():
    if request.method == 'POST':
        usuario = request.form['usuario']
        password = request.form['password']

        conn = sqlite3.connect('db.db')
        cur = conn.cursor()

        try:
            cur.execute("INSERT INTO users (usuario, password) VALUES (?, ?)", (usuario, password))
            conn.commit()
            conn.close()
            return redirect('/')
        except:
            conn.close()
            return render_template('registro.html', error="❌ Usuario ya existe")

    return render_template('registro.html')

# =========================
# PANEL USUARIO
# =========================
@app.route('/usuario')
def usuario():
    if 'user' not in session:
        return redirect('/')

    conn = sqlite3.connect('db.db')
    cur = conn.cursor()

    # LIBROS
    cur.execute("SELECT * FROM libros")
    libros = cur.fetchall()

    # PRESTAMOS DEL USUARIO
    cur.execute("""
    SELECT prestamos.id, libros.titulo, prestamos.fecha, prestamos.devuelto
    FROM prestamos
    JOIN libros ON libros.id = prestamos.libro_id
    WHERE prestamos.usuario = ?
    """, (session['user'],))
    prestamos = cur.fetchall()

    conn.close()

    return render_template('usuario.html', libros=libros, prestamos=prestamos)

# =========================
# PRESTAR LIBRO
# =========================
@app.route('/prestar/<int:id>', methods=['POST'])
def prestar(id):
    if 'user' not in session:
        return redirect('/')

    conn = sqlite3.connect('db.db')
    cur = conn.cursor()

    cur.execute("UPDATE libros SET disponible=0 WHERE id=?", (id,))
    cur.execute("INSERT INTO prestamos (usuario, libro_id, fecha, devuelto) VALUES (?, ?, date('now'), 0)",
                (session['user'], id))

    conn.commit()
    conn.close()

    return redirect('/usuario')

# =========================
# DEVOLVER LIBRO
# =========================
@app.route('/devolver/<int:id>', methods=['POST'])
def devolver(id):
    conn = sqlite3.connect('db.db')
    cur = conn.cursor()

    cur.execute("UPDATE prestamos SET devuelto=1 WHERE id=?", (id,))
    cur.execute("""
    UPDATE libros SET disponible=1 
    WHERE id = (SELECT libro_id FROM prestamos WHERE id=?)
    """, (id,))

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

# =========================
# RUN
# =========================
if __name__ == '__main__':
    app.run(debug=True)
