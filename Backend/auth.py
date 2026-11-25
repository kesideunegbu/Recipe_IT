"""Account and session endpoints: register, login, logout, and "who am I".

Other blueprints protect their routes with @login_required from here.
"""

import sqlite3
from functools import wraps

from flask import Blueprint, g, jsonify, request, session

from db import get_db
from passwords import (
    hash_password,
    needs_rehash,
    validate_password,
    verify_password,
)

bp = Blueprint("auth", __name__, url_prefix="/api")

# Longest valid email address (RFC 5321).
MAX_EMAIL_LENGTH = 254

# Verified against when the username doesn't exist, so a login for an unknown
# user takes as long as one with a wrong password. Without this, response time
# would reveal which usernames are registered.
_DUMMY_HASH = hash_password("dummy-password-for-timing")


def login_required(view):
    """Decorator for API routes that need a logged-in user.

    Returns 401 if nobody is logged in; otherwise sets g.user_id for the view.
    """

    @wraps(view)
    def wrapped(*args, **kwargs):
        user_id = session.get("user_id")
        if user_id is None:
            return jsonify(error="Please log in."), 401
        g.user_id = user_id
        return view(*args, **kwargs)

    return wrapped


def _read_credentials():
    data = request.get_json(silent=True) or {}
    email = data.get("email")
    password = data.get("password")
    if isinstance(email, str):
        email = email.strip()
    return email, password


def _is_valid_email(email):
    # A light check only; the real proof is a confirmation email later.
    if not isinstance(email, str) or len(email) > MAX_EMAIL_LENGTH:
        return False
    local, _, domain = email.partition("@")
    return bool(local) and "." in domain and " " not in email


@bp.post("/register")
def register():
    email, password = _read_credentials()
    if not _is_valid_email(email):
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


@bp.post("/login")
def login():
    email, password = _read_credentials()
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

    # Throw away any existing session first, so a session id planted
    # before login can't be reused afterwards (session fixation).
    session.clear()
    session["user_id"] = user["id"]
    session.permanent = True
    return jsonify(message="Logged in."), 200


@bp.post("/logout")
def logout():
    session.clear()
    return jsonify(message="Logged out."), 200


@bp.get("/me")
@login_required
def me():
    user = get_db().execute(
        "SELECT id, email FROM users WHERE id = ?", (g.user_id,)
    ).fetchone()
    if user is None:
        # The account was deleted after this cookie was issued.
        session.clear()
        return jsonify(error="Please log in."), 401
    return jsonify(id=user["id"], email=user["email"]), 200
