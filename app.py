from flask import Flask, request, jsonify
import sqlite3
from datetime import datetime, timedelta

app = Flask(__name__)

DB_FILE = "database.db"

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
    return "COC License Server (UPGRADED)"

# ---------------- GENERATE LICENSE ----------------
@app.route("/generate", methods=["POST"])
def generate():
    data = request.json
    key = data.get("license")
    days = int(data.get("days", 7))  # default 7 days

    expiry_date = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    try:
        c.execute(
            "INSERT INTO licenses (license_key, active, expiry) VALUES (?, 1, ?)",
            (key, expiry_date)
        )
        conn.commit()
        return jsonify({
            "status": "created",
            "license": key,
            "expiry": expiry_date
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

    # check active
    if active != 1:
        return jsonify({"status": "disabled"})

    # check expiry
    if expiry < today:
        return jsonify({"status": "expired"})

    # HWID bind (first time lock)
    if saved_hwid is None:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("UPDATE licenses SET hwid=? WHERE license_key=?", (hwid, key))
        conn.commit()
        conn.close()
        return jsonify({"status": "bound", "message": "HWID locked"})

    if saved_hwid != hwid:
        return jsonify({"status": "hwid mismatch"})

    return jsonify({"status": "valid"})

# ---------------- DISABLE LICENSE ----------------
@app.route("/disable", methods=["POST"])
def disable():
    data = request.json
    key = data.get("license")

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE licenses SET active=0 WHERE license_key=?", (key,))
    conn.commit()
    conn.close()

    return jsonify({"status": "disabled"})

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
