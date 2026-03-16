from flask import Blueprint, request, session
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
from pathlib import Path

auth_bp = Blueprint("auth", __name__)

DB_PATH = os.getenv("DB_PATH", "auth.db")

# ---------- DB HELPERS ----------

def get_db():
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as db:
        db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
        """)
        db.commit()

init_db()

# ---------- ROUTES ----------

@auth_bp.route("/signup", methods=["POST"])
def signup():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return {"error": "Missing fields"}, 400

    hashed = generate_password_hash(password)

    try:
        with get_db() as db:
            db.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, hashed)
            )
            db.commit()
    except sqlite3.IntegrityError:
        return {"error": "User already exists"}, 400

    return {"message": "Signup successful"}

@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    with get_db() as db:
        user = db.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,)
        ).fetchone()

    if not user or not check_password_hash(user["password"], password):
        return {"error": "Invalid credentials"}, 401

    session["user"] = username
    return {"message": "Login successful"}

@auth_bp.route("/me", methods=["GET"])
def me():
    if "user" in session:
        return {"user": session["user"]}
    return {"error": "Unauthorized"}, 401

@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return {"message": "Logged out"}
