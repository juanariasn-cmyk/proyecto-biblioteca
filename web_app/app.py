from flask import Flask, render_template, request, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash
import psycopg2, os

app = Flask(__name__)
app.secret_key = "pro_empresa"

UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# ================= DB ONLINE =================
def db():
    return psycopg2.connect(
        host="TU_HOST",
        database="postgres",
        user="postgres",
        password="TU_PASSWORD",
        port="5432"
    )

# ================= LOGIN =================
@app.route('/', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        u = request.form['usuario']
        p = request.form['password']

        conn = db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE usuario=%s", (u,))
        user = cur.fetchone()
        conn.close()

        if user and check_password_hash(user[2], p):
            session['user'] = u
            return redirect('/admin' if u == 'admin' else '/usuario')

        return render_template('login.html', error="Datos incorrectos")

    return render_template('login.html')

# ================= REGISTRO =================
@app.route('/registro', methods=['GET','POST'])
def registro():
    if request.method == 'POST':
        u = request.form['usuario']
        p = request.form['password']

        conn = db()
        cur = conn.cursor()

        try:
            cur.execute("INSERT INTO users(usuario,password) VALUES(%s,%s)",
                        (u, generate_password_hash(p)))
            conn.commit()
            conn.close()
            return redirect('/')
        except:
            conn.close()
            return render_template('register.html', error="Usuario ya existe")

    return render_template('register.html')

# ================= USUARIO =================
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
    WHERE prestamos.usuario=%s
    """, (session['user'],))

    prestamos = cur.fetchall()

    conn.close()

    return render_template('usuario.html', libros=libros, prestamos=prestamos)

# ================= ADMIN =================
@app.route('/admin', methods=['GET','POST'])
def admin():
    if 'user' not in session or session['user'] != 'admin':
        return redirect('/')

    conn = db()
    cur = conn.cursor()

    if request.method == 'POST':
        titulo = request.form['titulo']
        autor = request.form['autor']
        file = request.files['imagen']

        nombre = 'default.png'

        if file and file.filename != '':
            path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(path)
            nombre = file.filename

        cur.execute("INSERT INTO libros(titulo,autor,imagen,disponible) VALUES(%s,%s,%s,1)",
                    (titulo, autor, nombre))
        conn.commit()

    cur.execute("SELECT * FROM libros")
    libros = cur.fetchall()

    conn.close()

    return render_template('admin.html', libros=libros)

# ================= ELIMINAR =================
@app.route('/eliminar/<int:id>')
def eliminar(id):
    conn = db()
    cur = conn.cursor()
    cur.execute("DELETE FROM libros WHERE id=%s", (id,))
    conn.commit()
    conn.close()
    return redirect('/admin')

# ================= PRESTAR =================
@app.route('/prestar/<int:id>', methods=['POST'])
def prestar(id):
    conn = db()
    cur = conn.cursor()

    cur.execute("UPDATE libros SET disponible=0 WHERE id=%s", (id,))
    cur.execute("INSERT INTO prestamos(usuario,libro_id,fecha,devuelto) VALUES(%s,%s,CURRENT_DATE,0)",
                (session['user'], id))

    conn.commit()
    conn.close()
    return redirect('/usuario')

# ================= DEVOLVER =================
@app.route('/devolver/<int:id>', methods=['POST'])
def devolver(id):
    conn = db()
    cur = conn.cursor()

    cur.execute("UPDATE prestamos SET devuelto=1 WHERE id=%s", (id,))
    cur.execute("UPDATE libros SET disponible=1 WHERE id=(SELECT libro_id FROM prestamos WHERE id=%s)", (id,))

    conn.commit()
    conn.close()
    return redirect('/usuario')

# ================= BUSCAR =================
@app.route('/buscar')
def buscar():
    q = request.args.get('q')

    conn = db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM libros WHERE titulo ILIKE %s", ('%'+q+'%',))
    libros = cur.fetchall()
    conn.close()

    return render_template('usuario.html', libros=libros, prestamos=[])

# ================= DASHBOARD 📊 =================
@app.route('/dashboard')
def dashboard():
    if 'user' not in session or session['user'] != 'admin':
        return redirect('/')

    conn = db()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM libros")
    total_libros = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM users")
    total_users = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM prestamos WHERE devuelto=0")
    prestados = cur.fetchone()[0]

    conn.close()

    return render_template('dashboard.html',
                           total_libros=total_libros,
                           total_users=total_users,
                           prestados=prestados)

# ================= LOGOUT =================
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')
    
if __name__ == '__main__':
    app.run(debug=True)
