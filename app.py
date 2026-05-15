from flask import Flask, request, jsonify, render_template, redirect, session
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor
import random
import string
from datetime import datetime, timedelta
import os

app = Flask(__name__)
CORS(app)
app.secret_key = "LAKHAN_84411004778"

# ---------- DATABASE CONNECTION ----------
DATABASE_URL = os.environ.get('DATABASE_URL')
if not DATABASE_URL:
    raise Exception("DATABASE_URL environment variable not set!")

def get_db_connection():
    return psycopg2.connect(DATABASE_URL)

# ---------- INIT TABLE ----------
def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS licenses (
            id SERIAL PRIMARY KEY,
            license_key TEXT UNIQUE,
            hwid TEXT,
            active INTEGER DEFAULT 1,
            expiry TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

def generate_key():
    return ''.join(random.choices(string.ascii_uppercase, k=10)) + \
           ''.join(random.choices(string.digits, k=5))

# ---------- WEB PAGES ----------
@app.route("/")
def home():
    return "COC License Server Running"

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

@app.route("/dashboard")
def dashboard():
    if not session.get("admin"):
        return redirect("/login")
    return render_template("dashboard.html")

# ---------- API: GET ALL LICENSES (with HWID) ----------
@app.route("/api/licenses")
def api_licenses():
    if not session.get("admin"):
        return jsonify({"error": "unauthorized"}), 401
    conn = get_db_connection()
    c = conn.cursor(cursor_factory=RealDictCursor)
    c.execute("SELECT * FROM licenses ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()
    # Dashboard expects list of lists
    result = [[row['id'], row['license_key'], row['hwid'] or "", row['active'], row['expiry']] for row in rows]
    return jsonify(result)

# ---------- API: GENERATE ----------
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

    conn = get_db_connection()
    c = conn.cursor()
    c.execute(
        "INSERT INTO licenses (license_key, hwid, active, expiry) VALUES (%s, %s, %s, %s)",
        (key, "", 1, expiry)
    )
    conn.commit()
    conn.close()

    return jsonify({
        "status": "created",
        "license": key,
        "expiry": expiry
    })

# ---------- API: DELETE ----------
@app.route("/delete", methods=["POST"])
def delete():
    if not session.get("admin"):
        return jsonify({"status": "unauthorized"}), 401
    key = request.json.get("license")
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("DELETE FROM licenses WHERE license_key=%s", (key,))
    conn.commit()
    conn.close()
    return jsonify({"status": "deleted"})

# ---------- API: VALIDATE (with HWID binding & return expiry) ----------
@app.route("/validate", methods=["POST"])
def validate():
    data = request.json
    key = data.get("key")
    hwid = data.get("hwid")
    if not key:
        return jsonify({"valid": False})

    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT license_key, hwid, active, expiry FROM licenses WHERE license_key=%s", (key,))
    row = c.fetchone()

    if not row:
        conn.close()
        return jsonify({"valid": False, "message": "License key not found"})

    license_key, saved_hwid, active, expiry = row

    # Check active & expiry
    if active != 1:
        conn.close()
        return jsonify({"valid": False, "message": "License is inactive"})
    try:
        if expiry < datetime.now().strftime("%Y-%m-%d"):
            conn.close()
            return jsonify({"valid": False, "message": "License expired"})
    except:
        conn.close()
        return jsonify({"valid": False, "message": "Invalid expiry date"})

    # HWID binding logic
    if not saved_hwid:
        # First activation – save HWID
        c.execute("UPDATE licenses SET hwid=%s WHERE license_key=%s", (hwid, key))
        conn.commit()
    elif saved_hwid != hwid:
        conn.close()
        return jsonify({"valid": False, "message": "HWID mismatch. This license is locked to another device."})

    conn.close()
    return jsonify({"valid": True, "expiry": expiry})

# ---------- ADMIN CREDS ----------
ADMIN_API_KEY = "LAKHAN_84411004778"
ADMIN_USER = "lakhan_8956"
ADMIN_PASS = "Lakhan@21"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
