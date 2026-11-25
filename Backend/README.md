# Recipe_IT Backend

Flask API that turns the user's ingredients into recipes with Gemini Flash. Passwords are hashed with **Argon2id** (`passwords.py`). Plain-text passwords are never stored.

## Setup

```bash
cd Backend
python -m venv .venv
.venv\Scripts\activate        # Windows  (macOS/Linux: source .venv/bin/activate)
pip install -r requirements.txt
copy .env.example .env        # macOS/Linux: cp .env.example .env  — then fill it in
python app.py                 # development server: http://127.0.0.1:5000 (serves the Frontend pages too)
```

Run tests: `python -m pytest`

## Production server

`python Server\start_server.py` runs the app with Waitress, a production server. On Windows, `start_server.bat` in `Backend\Server` does the same using `Backend\.venv`. It binds to all interfaces by default so a hosting provider or another device on the network can reach it.

| Variable | Default | Description |
|---|---:|---|
| `HOST` | `0.0.0.0` | Interface to bind |
| `PORT` | `5000` | TCP port |
| `WAITRESS_THREADS` | `4` | Request worker threads |

When serving over HTTPS, also set `SESSION_COOKIE_SECURE=1` (see below).

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
| `GENERATE_PER_MINUTE` | Optional. Recipe generations each user may make per minute; default `10`. |
| `GENERATE_PER_DAY` | Optional. Recipe generations each user may make per 24 hours; default `100`. Caps what one account can cost. |
| `SESSION_COOKIE_SECURE` | Optional. Set to `1` when served over HTTPS so the cookie is never sent over plain HTTP. |
| `DATABASE_PATH` | Optional. SQLite file; default `Backend/recipe_it.db`. |

## Code layout

| File | What's in it |
|---|---|
| `app.py` | `create_app()`: loads config, sets up the database, registers blueprints |
| `config.py` | Reads settings from the environment / `.env` |
| `db.py` | `get_db()` connection per request, and `SCHEMA` (add new tables here) |
| `auth.py` | Blueprint for register / login / logout / me, and `@login_required` |
| `recipes.py` | Blueprint for `/api/recipes/*`; validates input |
| `generator.py` | Calls Gemini (fallback model, timeout) and cleans up its recipes |
| `ratelimit.py` | In-memory per-user limit on recipe generation |
| `passwords.py` | Argon2id hashing and password rules |

Tests never call Gemini: `conftest.py` hides `GEMINI_API_KEY`, and `test_recipes.py` swaps in a fake client via `app.extensions["recipe_generator"]`.

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

### Recipe generation

`POST /api/recipes/generate` (login required) turns ingredients into 3 recipes with Gemini. Usually takes a few seconds; allow up to 30.

Request:

```json
{ "ingredients": ["eggs", "rice", "spinach"], "servings": 2, "max_minutes": 30 }
```

- `ingredients`: 1–30 names, each up to 50 characters (letters, digits, spaces and `- ' & , . / ( )`). Trimmed, lowercased and de-duplicated.
- `servings`: optional, 1–12, default 2. `max_minutes`: optional, 5–240.

Response `200`:

```json
{
  "recipes": [
    {
      "title": "Garlic Egg Fried Rice",
      "description": "A quick and savory fried rice.",
      "ingredients": [
        { "name": "eggs", "amount": "2", "in_pantry": true },
        { "name": "soy sauce", "amount": "1 tablespoon", "in_pantry": false }
      ],
      "steps": ["Heat oil in a pan.", "Scramble the eggs.", "Add the rice and toss."],
      "prep_minutes": 15,
      "servings": 2
    }
  ],
  "ingredients": ["eggs", "rice", "spinach"],
  "model": "gemini-3.5-flash-lite"
}
```

`in_pantry: false` means the user needs to buy it. `prep_minutes` and `servings` may be `null`.

| Status | Meaning |
|---|---|
| `400` | Bad input (message says what) |
| `401` | Not logged in |
| `422` | Gemini couldn't make recipes from those ingredients |
| `429` | Too many generations (`GENERATE_PER_MINUTE` / `GENERATE_PER_DAY`); the `Retry-After` header gives the seconds to wait. Bad input (`400`) doesn't count |
| `502` | Gemini sent back something unusable |
| `503` | Gemini is busy (after trying the fallback model) or generation isn't configured |
| `504` | Gemini took longer than `GEMINI_TIMEOUT_SECONDS` |
