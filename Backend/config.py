"""Settings for Recipe_IT, read from environment variables.

Values come from the real environment first, then from Backend/.env (copy
.env.example to .env to get started). Secrets such as SECRET_KEY and
GEMINI_API_KEY live only in .env or the environment, never in git.
"""

import os
import secrets
import warnings
from datetime import timedelta

from dotenv import load_dotenv

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BACKEND_DIR, "..", "Frontend")

# override=False: a variable already set in the environment wins over .env.
load_dotenv(os.path.join(BACKEND_DIR, ".env"), override=False)

DEFAULT_DATABASE = os.path.join(BACKEND_DIR, "recipe_it.db")
# Flash-Lite is Google's lowest-latency model, which keeps recipe generation
# quick. Measured on a short recipe prompt: ~12s with minimal thinking versus
# ~35s with default thinking; gemini-3.6-flash was slower and often timed out.
DEFAULT_GEMINI_MODEL = "gemini-3.5-flash-lite"
# Tried when the main model is overloaded (503) or times out.
DEFAULT_GEMINI_FALLBACK_MODEL = "gemini-3.6-flash"
# How much the model "thinks" before answering. "minimal" is fastest and is
# plenty for recipes. (Gemini 3.x rejects thinking_budget=0; use this instead.)
DEFAULT_GEMINI_THINKING_LEVEL = "minimal"
# Give up on a Gemini call after this long, so the page never hangs.
DEFAULT_GEMINI_TIMEOUT_SECONDS = 30
# Recipe generations allowed per user. The per-minute cap stops bursts; the
# per-day cap bounds what one account can cost.
DEFAULT_GENERATE_PER_MINUTE = 10
DEFAULT_GENERATE_PER_DAY = 100

# How long a login lasts before the user has to sign in again.
SESSION_LIFETIME = timedelta(days=7)


def _secret_key():
    # The secret key signs the session cookie. Anyone who knows it can forge a
    # login as any user, so it must come from the environment, never from git.
    key = os.environ.get("SECRET_KEY")
    if key:
        return key
    warnings.warn(
        "SECRET_KEY is not set; using a random key. Everyone will be logged "
        "out whenever the server restarts. Set SECRET_KEY in Backend/.env."
    )
    return secrets.token_hex(32)


def load_config(database=None, secret_key=None):
    """Return the Flask config dict. Arguments override the environment (for tests)."""
    return {
        "DATABASE": database or os.environ.get("DATABASE_PATH") or DEFAULT_DATABASE,
        "SECRET_KEY": secret_key or _secret_key(),
        # JavaScript can't read the cookie, so an XSS bug can't steal it.
        "SESSION_COOKIE_HTTPONLY": True,
        # Browsers won't send the cookie on cross-site POSTs (CSRF defence).
        "SESSION_COOKIE_SAMESITE": "Lax",
        # Only send the cookie over HTTPS. Off by default so local
        # http://127.0.0.1 works; set SESSION_COOKIE_SECURE=1 when deployed.
        "SESSION_COOKIE_SECURE": os.environ.get("SESSION_COOKIE_SECURE") == "1",
        "PERMANENT_SESSION_LIFETIME": SESSION_LIFETIME,
        # Gemini settings. The key stays on the server; the browser never sees it.
        # A missing key isn't an error at startup: the recipe endpoint will
        # report that generation is unavailable instead.
        "GEMINI_API_KEY": os.environ.get("GEMINI_API_KEY") or None,
        "GEMINI_MODEL": os.environ.get("GEMINI_MODEL") or DEFAULT_GEMINI_MODEL,
        "GEMINI_FALLBACK_MODEL": os.environ.get("GEMINI_FALLBACK_MODEL")
        or DEFAULT_GEMINI_FALLBACK_MODEL,
        "GEMINI_THINKING_LEVEL": os.environ.get("GEMINI_THINKING_LEVEL")
        or DEFAULT_GEMINI_THINKING_LEVEL,
        "GEMINI_TIMEOUT_SECONDS": _positive_number(
            "GEMINI_TIMEOUT_SECONDS", DEFAULT_GEMINI_TIMEOUT_SECONDS
        ),
        "GENERATE_PER_MINUTE": _positive_int(
            "GENERATE_PER_MINUTE", DEFAULT_GENERATE_PER_MINUTE
        ),
        "GENERATE_PER_DAY": _positive_int(
            "GENERATE_PER_DAY", DEFAULT_GENERATE_PER_DAY
        ),
    }


def _positive_int(name, default):
    raw = os.environ.get(name)
    if not raw:
        return default
    try:
        value = int(raw)
    except ValueError:
        raise ValueError(f"{name} must be a whole number, got {raw!r}.")
    if value < 1:
        raise ValueError(f"{name} must be at least 1, got {raw!r}.")
    return value


def _positive_number(name, default):
    raw = os.environ.get(name)
    if not raw:
        return default
    try:
        value = float(raw)
    except ValueError:
        raise ValueError(f"{name} must be a number of seconds, got {raw!r}.")
    if value <= 0:
        raise ValueError(f"{name} must be greater than 0, got {raw!r}.")
    return value
