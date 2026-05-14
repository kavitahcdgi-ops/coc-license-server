from flask import Flask, request, jsonify, render_template, redirect, session
import sqlite3
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = "LAKHAN_84411004778"

DB_FILE = "database.db"

# ---------------- ADMIN CONFIG ----------------
ADMIN_USER = "lakhan_8956"
ADMIN_PASS = "Lakhan@21"

ADMIN_API_KEY = "LAKHAN_84411004778"

# ---------------- INIT DB ----------------
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

# ---------------- HOME ----------------
@app.route("/")
def home():
    return "COC License Server V2 Running"

# ---------------- ADMIN LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        u = request.form.get("username")
        p = request.form.get("password")

        if u == ADMIN_USER and p == ADMIN_PASS:
            session["admin"] = True
            return redirect("/dashboard")

        return "Invalid login"

    return '''
    <form method="POST">
        <input name="username" placeholder="Username">
        <input name="password" type="password" placeholder="Password">
        <button type="submit">Login</button>
    </form>
    '''

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

    return f"""
    <h1>License Dashboard</h1>
    <p>Total: {total}</p>
    <p>Active: {active}</p>
    <p>Inactive: {inactive}</p>
    <hr>
    <h3>All Licenses</h3>
    <pre>{data}</pre>
    <br><a href="/logout">Logout</a>
    """

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# ---------------- GENERATE LICENSE (SECURE) ----------------
@app.route("/generate", methods=["POST"])
def generate():
    api_key = request.headers.get("x-api-key")

    if api_key != ADMIN_API_KEY:
        return jsonify({"status": "unauthorized"}), 401

    data = request.json
    key = data.get("license")
    days = int(data.get("days", 7))

    expiry = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    try:
        c.execute(
            "INSERT INTO licenses (license_key, active, expiry) VALUES (?,?,?)",
            (key, 1, expiry)
        )
        conn.commit()

        return jsonify({
            "status": "created",
            "license": key,
            "days": days,
            "expiry": expiry
        })

    except:
        return jsonify({"status": "exists"})

    finally:
        conn.close()

# ---------------- VERIFY LICENSE ----------------
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

    # first time bind
    if saved_hwid is None:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("UPDATE licenses SET hwid=? WHERE license_key=?", (hwid, key))
        conn.commit()
        conn.close()
        return jsonify({"status": "bound"})

    if saved_hwid != hwid:
        return jsonify({"status": "hwid mismatch"})

    return jsonify({"status": "valid"})

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
