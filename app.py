from flask import Flask, request, jsonify, render_template, redirect, session
import sqlite3
import random
import string
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = "LAKHAN_84411004778"

DB_FILE = "database.db"

# ---------------- ADMIN ----------------
ADMIN_USER = "lakhan_8956"
ADMIN_PASS = "Lakhan@21"
ADMIN_API_KEY = "LAKHAN_84411004778"

# ---------------- DB ----------------
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

# ---------------- LOG ----------------
def add_log(key, action):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    c.execute(
        "INSERT INTO logs (license_key, action, time) VALUES (?,?,?)",
        (key, action, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    )

    conn.commit()
    conn.close()

# ---------------- RANDOM KEY GENERATOR ----------------
def generate_key():
    letters = ''.join(random.choices(string.ascii_uppercase, k=10))
    numbers = ''.join(random.choices(string.digits, k=5))
    return letters + numbers

# ---------------- HOME ----------------
@app.route("/")
def home():
    return "COC License Server V2 Running"

# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        u = request.form.get("username")
        p = request.form.get("password")

        if u == ADMIN_USER and p == ADMIN_PASS:
            session["admin"] = True
            return redirect("/dashboard")

        return "Invalid login"

    return """
    <form method="POST">
        <input name="username" placeholder="Username"><br><br>
        <input name="password" type="password" placeholder="Password"><br><br>
        <button type="submit">Login</button>
    </form>
    """

# ---------------- DASHBOARD ----------------
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

    return render_template(
        "dashboard.html",
        data=data,
        total=total,
        active=active,
        inactive=inactive
    )

# ---------------- GENERATE ----------------
@app.route("/generate", methods=["POST"])
def generate():
    if request.headers.get("x-api-key") != ADMIN_API_KEY:
        return jsonify({"status": "unauthorized"}), 401

    data = request.json
    days = int(data.get("days", 7))

    key = generate_key()
    expiry = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    try:
        c.execute(
            "INSERT INTO licenses (license_key, active, expiry) VALUES (?,?,?)",
            (key, 1, expiry)
        )
        conn.commit()

        add_log(key, "generated")

        return jsonify({
            "status": "created",
            "license": key,
            "expiry": expiry
        })

    except:
        return jsonify({"status": "error"})

    finally:
        conn.close()

# ---------------- VERIFY ----------------
@app.route("/verify", methods=["POST"])
def verify():
    data = request.json
    key = data.get("license")
    hwid = data.get("hwid")

    today = datetime.now().strftime("%Y-%m-%d")

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    c.execute("SELECT hwid, expiry, active FROM licenses WHERE license_key=?", (key,))
    row = c.fetchone()
    conn.close()

    if not row:
        return jsonify({"status": "invalid"})

    saved_hwid, expiry, active = row

    if active != 1:
        return jsonify({"status": "disabled"})

    if expiry < today:
        return jsonify({"status": "expired"})

    if saved_hwid is None:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("UPDATE licenses SET hwid=? WHERE license_key=?", (hwid, key))
        conn.commit()
        conn.close()

        add_log(key, "bound")

        return jsonify({"status": "bound"})

    if saved_hwid != hwid:
        return jsonify({"status": "hwid mismatch"})

    add_log(key, "verified")

    return jsonify({"status": "valid"})

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

    add_log(key, "deleted")

    return jsonify({"status": "deleted"})

# ---------------- EXTEND ----------------
@app.route("/extend", methods=["POST"])
def extend():
    if not session.get("admin"):
        return jsonify({"status": "unauthorized"})

    key = request.json.get("license")
    days = int(request.json.get("days", 7))

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    c.execute("SELECT expiry FROM licenses WHERE license_key=?", (key,))
    row = c.fetchone()

    if not row:
        return jsonify({"status": "not found"})

    old = datetime.strptime(row[0], "%Y-%m-%d")
    new_expiry = (old + timedelta(days=days)).strftime("%Y-%m-%d")

    c.execute("UPDATE licenses SET expiry=? WHERE license_key=?", (new_expiry, key))
    conn.commit()
    conn.close()

    add_log(key, f"extended +{days}")

    return jsonify({"status": "extended", "expiry": new_expiry})

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
