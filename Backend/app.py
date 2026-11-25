"""Recipe_IT backend: builds the Flask app from its parts.

Run with:  python app.py   then open http://127.0.0.1:5000

    config.py    settings from environment variables / .env
    db.py        database connection and schema
    auth.py      register, login, logout, /api/me, @login_required
    recipes.py   /api/recipes/generate
    generator.py calls Gemini and cleans up its recipes
    passwords.py Argon2id password hashing
"""

import logging

from flask import Flask, redirect, session

import auth
import db
import recipes
from config import FRONTEND_DIR, load_config
from generator import RecipeGenerator


def create_app(database=None, secret_key=None):
    # static_url_path="" serves Frontend/login.html at /login.html, so the
    # page's relative links (login.css, images/...) keep working. Serving the
    # frontend from Flask keeps pages and API on one origin, so no CORS needed.
    app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path="")
    app.config.update(load_config(database=database, secret_key=secret_key))

    db.init_app(app)
    app.register_blueprint(auth.bp)
    app.register_blueprint(recipes.bp)

    # One Gemini client for the whole app (None if GEMINI_API_KEY is unset;
    # the generate endpoint then answers 503). Tests swap in a fake here.
    app.extensions["recipe_generator"] = RecipeGenerator.from_config(app.config)
    if app.extensions["recipe_generator"] is None:
        logging.getLogger(__name__).warning(
            "GEMINI_API_KEY is not set; recipe generation is disabled."
        )

    @app.get("/")
    def index():
        if session.get("user_id") is not None:
            return redirect("/index.html")
        return redirect("/login.html")

    return app


if __name__ == "__main__":
    create_app().run(debug=True)
