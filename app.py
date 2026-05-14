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

# ---------------- INIT DATABASE ----------------
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
    return "COC License Server Running (V2)"

# ---------------- RUN SERVER ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
