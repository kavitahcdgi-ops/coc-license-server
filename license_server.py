from fastapi import FastAPI
from pydantic import BaseModel
import sqlite3
import datetime

app = FastAPI()

DB = "licenses.db"

# =========================
# INIT DATABASE
# =========================

def init_db():

    conn = sqlite3.connect(DB)

    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS licenses (
        license_key TEXT PRIMARY KEY,
        hwid TEXT,
        expiry TEXT,
        active INTEGER
    )
    """)

    conn.commit()
    conn.close()

init_db()

# =========================
# REQUEST MODEL
# =========================

class LicenseRequest(BaseModel):
    license_key: str
    hwid: str

# =========================
# TEST ROUTE
# =========================

@app.get("/")

def home():

    return {
        "status": "online",
        "message": "COC LICENSE SERVER RUNNING"
    }

# =========================
# VALIDATE LICENSE
# =========================

@app.post("/validate")

def validate_license(data: LicenseRequest):

    conn = sqlite3.connect(DB)

    c = conn.cursor()

    c.execute(
        "SELECT hwid, expiry, active FROM licenses WHERE license_key=?",
        (data.license_key,)
    )

    row = c.fetchone()

    if not row:

        return {
            "status": "invalid",
            "message": "KEY NOT FOUND"
        }

    saved_hwid, expiry, active = row

    if active != 1:

        return {
            "status": "invalid",
            "message": "LICENSE DISABLED"
        }

    today = datetime.date.today()

    if today > datetime.date.fromisoformat(expiry):

        return {
            "status": "expired",
            "message": "LICENSE EXPIRED"
        }

    # FIRST ACTIVATION

    if not saved_hwid:

        c.execute(
            "UPDATE licenses SET hwid=? WHERE license_key=?",
            (data.hwid, data.license_key)
        )

        conn.commit()

    # HWID CHECK

    elif saved_hwid != data.hwid:

        return {
            "status": "invalid",
            "message": "HWID MISMATCH"
        }

    return {
        "status": "valid",
        "message": "LICENSE OK",
        "expiry": expiry
    }
