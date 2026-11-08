# Recipe_IT Backend

Flask API. Passwords are hashed with **Argon2id** (`passwords.py`). Plain-text passwords are never stored.

## Setup

```bash
cd Backend
python -m venv .venv
.venv\Scripts\activate        # Windows  (macOS/Linux: source .venv/bin/activate)
pip install -r requirements.txt
python Server\start_server.py # serves the Frontend pages and API
```

Run tests: `python -m pytest`

From `Backend\Server` on Windows, `start_server.bat` runs the same production
server using `Backend\.venv`. The server binds to all interfaces by default so
it can be reached by a hosting provider or another device on the network.

Configure hosting with environment variables:

| Variable | Default | Description |
|---|---:|---|
| `HOST` | `0.0.0.0` | Interface to bind |
| `PORT` | `5000` | TCP port |
| `WAITRESS_THREADS` | `4` | Request worker threads |

For local development, `python app.py` still starts Flask's development server.

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
