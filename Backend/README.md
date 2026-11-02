# Recipe_IT Backend

Flask API. Passwords are hashed with **Argon2id** (`passwords.py`). Plain-text passwords are never stored.

## Setup

```bash
cd Backend
python -m venv .venv
.venv\Scripts\activate        # Windows  (macOS/Linux: source .venv/bin/activate)
pip install -r requirements.txt
python app.py                 # http://127.0.0.1:5000
```

Run tests: `python -m pytest`

## Endpoints (for the login page)

Both take JSON: `{"username": "...", "password": "..."}`

| Endpoint | Success | Errors |
|---|---|---|
| `POST /api/register` | `201 {"message": "Account created."}` | `400` invalid input, `409` username taken |
| `POST /api/login` | `200 {"message": "Logged in."}` | `400` missing fields, `401` wrong username/password |

Errors come back as `{"error": "message to show the user"}`. Passwords must be 8–128 characters.

```js
const res = await fetch("http://127.0.0.1:5000/api/login", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ username, password }),
});
const data = await res.json();   // data.message or data.error
```
