from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = "secret123"

def db():
    return sqlite3.connect("db.db")

@app.route("/", methods=["GET","POST"])
def login():
    if request.method == "POST":
        u = request.form["user"]
        p = request.form["password"]
        conn = db(); cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE user=? AND pass=?", (u,p))
        if cur.fetchone():
            session["user"]=u
            return redirect("/home")
    return render_template("login.html")

@app.route("/home")
def home():
    return render_template("home.html")

app.run()
