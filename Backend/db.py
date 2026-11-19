"""SQLite connection handling and schema for Recipe_IT.

Use get_db() inside a request to get a connection; it is closed automatically
when the request ends. Add new tables to SCHEMA.
"""

import sqlite3

from flask import current_app, g

# CREATE TABLE IF NOT EXISTS keeps this safe to run on every startup.
SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL COLLATE NOCASE,
    password_hash TEXT NOT NULL
);
"""


def get_db():
    """Return this request's database connection, opening it if needed."""
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
        # SQLite ignores foreign keys unless asked, per connection.
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(_exc=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_app(app):
    """Create the tables and make Flask close connections after each request."""
    app.teardown_appcontext(close_db)
    with app.app_context():
        db = get_db()
        db.executescript(SCHEMA)
        db.commit()
