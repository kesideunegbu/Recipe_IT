# Recipe_IT Backend

Flask API. Passwords are hashed with **Argon2id** (`passwords.py`). Plain-text passwords are never stored.

## Setup

```bash
cd Backend
python -m venv .venv
.venv\Scripts\activate        # Windows  (macOS/Linux: source .venv/bin/activate)
pip install -r requirements.txt
python app.py                 # open http://127.0.0.1:5000 (serves the Frontend pages too)
```

Run tests: `python -m pytest`

## Endpoints (for the login page)

Both take JSON: `{"email": "...", "password": "..."}`

| Endpoint | Success | Errors |
|---|---|---|
| `POST /api/register` | `201 {"message": "Account created."}` | `400` invalid email or password, `409` email already registered |
| `POST /api/login` | `200 {"message": "Logged in."}` | `400` missing fields, `401` wrong email/password |

Errors come back as `{"error": "message to show the user"}`. Passwords must be 8–128 characters.

```js
const res = await fetch("/api/login", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ email, password }),
});
const data = await res.json();   // data.message or data.error
```
