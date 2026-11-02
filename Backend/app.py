"""Recipe_IT backend: register and login endpoints.

Run with:  python app.py   (serves on http://127.0.0.1:5000)
"""

import os
import sqlite3

from flask import Flask, g, jsonify, request

from passwords import (
    hash_password,
    needs_rehash,
    validate_password,
    verify_password,
)

DEFAULT_DATABASE = os.path.join(os.path.dirname(__file__), "recipe_it.db")

# Verified against when the username doesn't exist, so a login for an unknown
# user takes as long as one with a wrong password. Without this, response time
# would reveal which usernames are registered.
_DUMMY_HASH = hash_password("dummy-password-for-timing")


def create_app(database=DEFAULT_DATABASE):
    app = Flask(__name__)
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
                   username TEXT UNIQUE NOT NULL COLLATE NOCASE,
                   password_hash TEXT NOT NULL
               )"""
        )
        get_db().commit()

    def read_credentials():
        data = request.get_json(silent=True) or {}
        username = data.get("username")
        password = data.get("password")
        if isinstance(username, str):
            username = username.strip()
        return username, password

    @app.post("/api/register")
    def register():
        username, password = read_credentials()
        if not isinstance(username, str) or not username:
            return jsonify(error="Username is required."), 400
        error = validate_password(password)
        if error:
            return jsonify(error=error), 400

        db = get_db()
        try:
            db.execute(
                "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                (username, hash_password(password)),
            )
            db.commit()
        except sqlite3.IntegrityError:
            return jsonify(error="That username is already taken."), 409
        return jsonify(message="Account created."), 201

    @app.post("/api/login")
    def login():
        username, password = read_credentials()
        if not isinstance(username, str) or not isinstance(password, str):
            return jsonify(error="Username and password are required."), 400

        db = get_db()
        user = db.execute(
            "SELECT id, password_hash FROM users WHERE username = ?", (username,)
        ).fetchone()

        if user is None:
            verify_password(_DUMMY_HASH, password)
            return jsonify(error="Invalid username or password."), 401
        if not verify_password(user["password_hash"], password):
            return jsonify(error="Invalid username or password."), 401

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
