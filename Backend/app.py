"""Recipe_IT backend: builds the Flask app from its parts.

Run with:  python app.py   then open http://127.0.0.1:5000

    config.py    settings from environment variables / .env
    db.py        database connection and schema
    auth.py      register, login, logout, /api/me, @login_required
    passwords.py Argon2id password hashing
"""

from flask import Flask, redirect, session

import auth
import db
from config import FRONTEND_DIR, load_config


def create_app(database=None, secret_key=None):
    # static_url_path="" serves Frontend/login.html at /login.html, so the
    # page's relative links (login.css, images/...) keep working. Serving the
    # frontend from Flask keeps pages and API on one origin, so no CORS needed.
    app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path="")
    app.config.update(load_config(database=database, secret_key=secret_key))

    db.init_app(app)
    app.register_blueprint(auth.bp)

    @app.get("/")
    def index():
        if session.get("user_id") is not None:
            return redirect("/index.html")
        return redirect("/login.html")

    return app


if __name__ == "__main__":
    create_app().run(debug=True)
