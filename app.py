from flask import Flask, request, jsonify, render_template, redirect, session
import sqlite3
import random
import string
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = "LAKHAN_84411004778"

DB_FILE = "database.db"

# 🔥 ADMIN CONFIG
ADMIN_API_KEY = "LAKHAN_84411004778"
ADMIN_USER = "lakhan_8956"
ADMIN_PASS = "Lakhan@21"

# ---------------- DB INIT ----------------
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

    conn.commit()
    conn.close()

init_db()

# ---------------- KEY GEN ----------------
def generate_key():
    return ''.join(random.choices(string.ascii_uppercase, k=10)) + \
           ''.join(random.choices(string.digits, k=5))

# ---------------- HOME ----------------
@app.route("/")
def home():
    return "COC License Server Running"

# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form.get("username") == ADMIN_USER and request.form.get("password") == ADMIN_PASS:
            session["admin"] = True
            return redirect("/dashboard")
        return "Invalid login"

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():
    if not session.get("admin"):
        return redirect("/login")
    return render_template("dashboard.html")

# ---------------- LIVE DATA ----------------
@app.route("/api/licenses")
def api_licenses():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM licenses ORDER BY id DESC")
    data = c.fetchall()
    conn.close()
    return jsonify(data)

# ---------------- GENERATE ----------------
@app.route("/generate", methods=["POST"])
def generate():
    if request.headers.get("x-api-key") != ADMIN_API_KEY:
        return jsonify({"status": "unauthorized"}), 401

    try:
        data = request.json or {}
        days = int(str(data.get("days", 7)).strip())
        if days <= 0:
            return jsonify({"status": "invalid_days"}), 400
    except:
        return jsonify({"status": "invalid_input"}), 400

    key = generate_key()
    expiry = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(
        "INSERT INTO licenses (license_key, hwid, active, expiry) VALUES (?,?,?,?)",
        (key, "", 1, expiry)
    )
    conn.commit()
    conn.close()

    return jsonify({
        "status": "created",
        "license": key,
        "expiry": expiry
    })

# ---------------- DELETE ----------------
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
    return jsonify({"status": "deleted"})

# =========================================================
# ✅ VALIDATION ENDPOINT (client yahi use karega)
# =========================================================
@app.route("/validate", methods=["POST"])
def validate():
    data = request.json
    key = data.get("key")

    if not key:
        return jsonify({"valid": False})

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(
        "SELECT license_key, active, expiry FROM licenses WHERE license_key=?",
        (key,)
    )
    row = c.fetchone()
    conn.close()

    if not row:
        return jsonify({"valid": False})

    license_key, active, expiry = row

    if active != 1:
        return jsonify({"valid": False})

    try:
        if expiry < datetime.now().strftime("%Y-%m-%d"):
            return jsonify({"valid": False})
    except:
        return jsonify({"valid": False})

    return jsonify({"valid": True})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
