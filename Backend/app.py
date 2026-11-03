"""Recipe_IT backend: register and login endpoints, plus the frontend pages.

Run with:  python app.py   then open http://127.0.0.1:5000
"""

import os
import sqlite3

from flask import Flask, g, jsonify, redirect, request

from passwords import (
    hash_password,
    needs_rehash,
    validate_password,
    verify_password,
)

DEFAULT_DATABASE = os.path.join(os.path.dirname(__file__), "recipe_it.db")
# Serving the frontend from Flask keeps the pages and the API on the same
# origin, so the browser allows the login page to call /api/* without CORS.
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Frontend")

# Longest valid email address (RFC 5321).
MAX_EMAIL_LENGTH = 254

# Verified against when the username doesn't exist, so a login for an unknown
# user takes as long as one with a wrong password. Without this, response time
# would reveal which usernames are registered.
_DUMMY_HASH = hash_password("dummy-password-for-timing")


def create_app(database=DEFAULT_DATABASE):
    # static_url_path="" serves Frontend/login.html at /login.html, so the
    # page's relative links (login.css, images/...) keep working.
    app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path="")
    app.config["DATABASE"] = database

    def get_db():
        if "db" not in g:
            g.db = sqlite3.connect(app.config["DATABASE"])
            g.db.row_factory = sqlite3.Row
        return g.db

    @app.teardown_appcontext
    def close_db(_exc):
        db = g.pop("db", None)
        if db is not None:
            db.close()

    with app.app_context():
        get_db().execute(
            """CREATE TABLE IF NOT EXISTS users (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   email TEXT UNIQUE NOT NULL COLLATE NOCASE,
                   password_hash TEXT NOT NULL
               )"""
        )
        get_db().commit()

    def read_credentials():
        data = request.get_json(silent=True) or {}
        email = data.get("email")
        password = data.get("password")
        if isinstance(email, str):
            email = email.strip()
        return email, password

    def is_valid_email(email):
        # A light check only; the real proof is a confirmation email later.
        if not isinstance(email, str) or len(email) > MAX_EMAIL_LENGTH:
            return False
        local, _, domain = email.partition("@")
        return bool(local) and "." in domain and " " not in email

    @app.get("/")
    def index():
        return redirect("/login.html")

    @app.post("/api/register")
    def register():
        email, password = read_credentials()
        if not is_valid_email(email):
            return jsonify(error="Please enter a valid email."), 400
        error = validate_password(password)
        if error:
            return jsonify(error=error), 400

        db = get_db()
        try:
            db.execute(
                "INSERT INTO users (email, password_hash) VALUES (?, ?)",
                (email, hash_password(password)),
            )
            db.commit()
        except sqlite3.IntegrityError:
            return jsonify(error="An account with that email already exists."), 409
        return jsonify(message="Account created."), 201

    @app.post("/api/login")
    def login():
        email, password = read_credentials()
        if not isinstance(email, str) or not isinstance(password, str):
            return jsonify(error="Email and password are required."), 400

        db = get_db()
        user = db.execute(
            "SELECT id, password_hash FROM users WHERE email = ?", (email,)
        ).fetchone()

        if user is None:
            verify_password(_DUMMY_HASH, password)
            return jsonify(error="Invalid email or password."), 401
        if not verify_password(user["password_hash"], password):
            return jsonify(error="Invalid email or password."), 401

        if needs_rehash(user["password_hash"]):
            db.execute(
                "UPDATE users SET password_hash = ? WHERE id = ?",
                (hash_password(password), user["id"]),
            )
            db.commit()

        # TODO (next sprint): start a session or issue a token here.
        return jsonify(message="Logged in."), 200

    return app


if __name__ == "__main__":
    create_app().run(debug=True)
