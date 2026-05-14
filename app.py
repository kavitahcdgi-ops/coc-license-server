from flask import Flask, request, jsonify
import sqlite3
import os

app = Flask(__name__)

DB_FILE = "database.db"

# ---------------- DB INIT ----------------
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS licenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            license_key TEXT UNIQUE,
            active INTEGER DEFAULT 1
        )
    """)
    conn.commit()
    conn.close()

init_db()

# ---------------- HOME ----------------
@app.route("/")
def home():
    return "COC License Server Running (SQLite)"

# ---------------- VERIFY ----------------
@app.route("/verify", methods=["POST"])
def verify():
    data = request.json
    key = data.get("license")

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT active FROM licenses WHERE license_key=?", (key,))
    row = c.fetchone()
    conn.close()

    if row and row[0] == 1:
        return jsonify({"status": "valid"})
    return jsonify({"status": "invalid"})

# ---------------- GENERATE ----------------
@app.route("/generate", methods=["POST"])
def generate():
    data = request.json
    key = data.get("license")

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    try:
        c.execute("INSERT INTO licenses (license_key, active) VALUES (?, 1)", (key,))
        conn.commit()
        return jsonify({"status": "created", "license": key})
    except:
        return jsonify({"status": "exists"})
    finally:
        conn.close()

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)
