from flask import Flask, request, jsonify, render_template, redirect, session
import sqlite3
import random
import string
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = "LAKHAN_84411004778"

DB_FILE = "database.db"

ADMIN_USER = "lakhan_8956"
ADMIN_PASS = "Lakhan@21"
ADMIN_API_KEY = "LAKHAN_84411004778"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS licenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            license_key TEXT UNIQUE,
            hwid TEXT,
            active INTEGER DEFAULT 1,
            expiry TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            license_key TEXT,
            action TEXT,
            time TEXT
        )
    """)

    conn.commit()
    conn.close()

init_db()

def add_log(key, action):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO logs (license_key, action, time) VALUES (?,?,?)",
              (key, action, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

def generate_key():
    return ''.join(random.choices(string.ascii_uppercase, k=10)) + ''.join(random.choices(string.digits, k=5))

@app.route("/")
def home():
    return "COC License Server V2 Running"

# ---------------- LOGIN (NOW UI PAGE) ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        u = request.form.get("username")
        p = request.form.get("password")

        if u == ADMIN_USER and p == ADMIN_PASS:
            session["admin"] = True
            return redirect("/dashboard")

        return "Invalid login"

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

@app.route("/dashboard")
def dashboard():
    if not session.get("admin"):
        return redirect("/login")

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM licenses")
    total = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM licenses WHERE active=1")
    active = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM licenses WHERE active=0")
    inactive = c.fetchone()[0]

    c.execute("SELECT * FROM licenses ORDER BY id DESC")
    data = c.fetchall()

    conn.close()

    return render_template("dashboard.html",
                           data=data,
                           total=total,
                           active=active,
                           inactive=inactive)

@app.route("/generate", methods=["POST"])
def generate():
    if request.headers.get("x-api-key") != ADMIN_API_KEY:
        return jsonify({"status": "unauthorized"}), 401

    days = int(request.json.get("days", 7))
    key = generate_key()

    expiry = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    c.execute("INSERT INTO licenses (license_key, active, expiry) VALUES (?,?,?)",
              (key, 1, expiry))
    conn.commit()
    conn.close()

    add_log(key, "generated")

    return jsonify({"status": "created", "license": key})

@app.route("/delete", methods=["POST"])
def delete():
    if not session.get("admin"):
        return jsonify({"status": "unauthorized"})

    key = request.json.get("license")

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM licenses WHERE license_key=?", (key,))
    conn.commit()
    conn.close()

    add_log(key, "deleted")

    return jsonify({"status": "deleted"})

@app.route("/extend", methods=["POST"])
def extend():
    if not session.get("admin"):
        return jsonify({"status": "unauthorized"})

    key = request.json.get("license")
    days = int(request.json.get("days", 7))

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    c.execute("SELECT expiry FROM licenses WHERE license_key=?", (key,))
    old = c.fetchone()[0]

    new_exp = (datetime.strptime(old, "%Y-%m-%d") + timedelta(days=days)).strftime("%Y-%m-%d")

    c.execute("UPDATE licenses SET expiry=? WHERE license_key=?", (new_exp, key))
    conn.commit()
    conn.close()

    add_log(key, f"extended {days}")

    return jsonify({"status": "extended"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
