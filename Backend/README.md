# Recipe_IT Backend

Flask API that turns the user's ingredients into recipes with Gemini Flash. Passwords are hashed with **Argon2id** (`passwords.py`). Plain-text passwords are never stored.

## Setup

```bash
cd Backend
python -m venv .venv
.venv\Scripts\activate        # Windows  (macOS/Linux: source .venv/bin/activate)
pip install -r requirements.txt
copy .env.example .env        # macOS/Linux: cp .env.example .env  — then fill it in
python app.py                 # open http://127.0.0.1:5000 (serves the Frontend pages too)
```

Run tests: `python -m pytest`

## Configuration (`.env`)

Settings are read from environment variables, falling back to `Backend/.env`. `.env` is git-ignored; **never commit it**. `.env.example` lists every setting.

| Variable | Purpose |
|---|---|
| `SECRET_KEY` | Signs session cookies. If missing, a random key is used and everyone is logged out on restart. Generate one with `python -c "import secrets; print(secrets.token_hex(32))"`. |
| `GEMINI_API_KEY` | Gemini API key ([get one](https://aistudio.google.com/apikey)). Used only on the server; never send it to the frontend. |
| `GEMINI_MODEL` | Optional. Model for recipe generation; default `gemini-3.5-flash-lite` (Google's fastest). |
| `GEMINI_FALLBACK_MODEL` | Optional. Tried when the main model is overloaded or times out; default `gemini-3.6-flash`. |
| `GEMINI_THINKING_LEVEL` | Optional. How much the model reasons before answering; default `minimal` (fastest, ~3× quicker than the model's default in testing). |
| `GEMINI_TIMEOUT_SECONDS` | Optional. Give up on a Gemini call after this many seconds; default `30`. |
| `SESSION_COOKIE_SECURE` | Optional. Set to `1` when served over HTTPS so the cookie is never sent over plain HTTP. |
| `DATABASE_PATH` | Optional. SQLite file; default `Backend/recipe_it.db`. |

## Code layout

| File | What's in it |
|---|---|
| `app.py` | `create_app()`: loads config, sets up the database, registers blueprints |
| `config.py` | Reads settings from the environment / `.env` |
| `db.py` | `get_db()` connection per request, and `SCHEMA` (add new tables here) |
| `auth.py` | Blueprint for register / login / logout / me, and `@login_required` |
| `passwords.py` | Argon2id hashing and password rules |

New features go in their own blueprint module (for example `pantry.py`), registered in `create_app()`. Protect their routes with `@login_required` from `auth.py`: it returns `401` when nobody is logged in and otherwise sets `g.user_id`.

## Endpoints

All take and return JSON. Errors come back as `{"error": "message to show the user"}`.

### Accounts

Both take `{"email": "...", "password": "..."}`. Passwords must be 8–128 characters.

| Endpoint | Success | Errors |
|---|---|---|
| `POST /api/register` | `201 {"message": "Account created."}` | `400` invalid email or password, `409` email already registered |
| `POST /api/login` | `200 {"message": "Logged in."}` | `400` missing fields, `401` wrong email/password |

```js
const res = await fetch("/api/login", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ email, password }),
});
const data = await res.json();   // data.message or data.error
```

Registering does **not** log the user in; call `/api/login` afterwards.

### Sessions

A successful login sets a signed, HttpOnly session cookie (valid 7 days). The browser sends it automatically on later requests to the same site.

| Endpoint | Success | Errors |
|---|---|---|
| `GET /api/me` | `200 {"id": 1, "email": "..."}` | `401` not logged in |
| `POST /api/logout` | `200 {"message": "Logged out."}` | — |

Pages that need a login include `<script src="auth.js" defer></script>`, which redirects to the login page when the user isn't logged in.
