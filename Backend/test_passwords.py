import pytest

from app import create_app
from passwords import hash_password, needs_rehash, verify_password


# --- passwords.py -----------------------------------------------------------

def test_hash_is_not_the_plain_password():
    hashed = hash_password("correct horse battery")
    assert "correct horse battery" not in hashed
    assert hashed.startswith("$argon2id$")


def test_same_password_gets_different_hashes():
    # Each hash uses a fresh random salt.
    assert hash_password("samepassword") != hash_password("samepassword")


def test_verify_correct_and_wrong_password():
    hashed = hash_password("correct horse battery")
    assert verify_password(hashed, "correct horse battery")
    assert not verify_password(hashed, "wrong password")
    assert not verify_password(hashed, "Correct horse battery")


def test_verify_handles_garbage_hash():
    assert not verify_password("not-a-real-hash", "whatever123")


def test_rejects_short_and_too_long_passwords():
    with pytest.raises(ValueError):
        hash_password("short")
    with pytest.raises(ValueError):
        hash_password("x" * 129)


def test_fresh_hash_does_not_need_rehash():
    assert not needs_rehash(hash_password("password123"))


# --- API endpoints ----------------------------------------------------------

@pytest.fixture
def client(tmp_path):
    app = create_app(database=str(tmp_path / "test.db"), secret_key="test-secret")
    return app.test_client()


def register(client, email="alice@example.com", password="password123"):
    return client.post("/api/register", json={"email": email, "password": password})


def login(client, email="alice@example.com", password="password123"):
    return client.post("/api/login", json={"email": email, "password": password})


def test_register_then_login(client):
    assert register(client).status_code == 201
    assert login(client).status_code == 200


def test_login_wrong_password(client):
    register(client)
    assert login(client, password="wrongpass1").status_code == 401


def test_login_unknown_user_gives_same_error(client):
    register(client)
    unknown = login(client, email="bob@example.com")
    wrong = login(client, password="wrongpass1")
    assert unknown.status_code == wrong.status_code == 401
    assert unknown.get_json() == wrong.get_json()


def test_duplicate_email_rejected(client):
    register(client)
    assert register(client, email="ALICE@example.com").status_code == 409


@pytest.mark.parametrize("email", ["", "alice", "alice@", "@example.com", "alice@localhost", "a b@example.com"])
def test_register_rejects_invalid_email(client, email):
    assert register(client, email=email).status_code == 400


def test_register_rejects_weak_password(client):
    assert register(client, password="short").status_code == 400


def test_password_stored_as_hash(client, tmp_path):
    import sqlite3

    register(client)
    row = sqlite3.connect(tmp_path / "test.db").execute(
        "SELECT password_hash FROM users WHERE email = 'alice@example.com'"
    ).fetchone()
    assert row[0].startswith("$argon2id$")
    assert "password123" not in row[0]


def test_serves_login_page(client):
    assert client.get("/").headers["Location"].endswith("/login.html")
    page = client.get("/login.html")
    assert page.status_code == 200
    assert b'id="login-form"' in page.data
    assert client.get("/login.css").status_code == 200
    assert client.get("/login.js").status_code == 200
    assert client.get("/images/recipe-background.jpg").status_code == 200


# --- sessions ---------------------------------------------------------------

def test_me_requires_login(client):
    assert client.get("/api/me").status_code == 401


def test_login_starts_session(client):
    register(client)
    login(client)
    me = client.get("/api/me")
    assert me.status_code == 200
    assert me.get_json()["email"] == "alice@example.com"


def test_failed_login_does_not_start_session(client):
    register(client)
    login(client, password="wrongpass1")
    assert client.get("/api/me").status_code == 401


def test_register_does_not_log_in(client):
    register(client)
    assert client.get("/api/me").status_code == 401


def test_logout_ends_session(client):
    register(client)
    login(client)
    assert client.post("/api/logout").status_code == 200
    assert client.get("/api/me").status_code == 401


def test_session_cookie_flags(client):
    register(client)
    cookie = login(client).headers["Set-Cookie"]
    assert "HttpOnly" in cookie
    assert "SameSite=Lax" in cookie
    assert "password123" not in cookie


def test_forged_cookie_rejected(client, tmp_path):
    # A session cookie signed with a different key must not be accepted.
    other = create_app(database=str(tmp_path / "test.db"), secret_key="attacker-key")
    other_client = other.test_client()
    register(client)
    login(other_client)
    forged = other_client.get_cookie("session").value
    client.set_cookie("session", forged)
    assert client.get("/api/me").status_code == 401


def test_deleted_user_session_is_cleared(client, tmp_path):
    import sqlite3

    register(client)
    login(client)
    db = sqlite3.connect(tmp_path / "test.db")
    db.execute("DELETE FROM users")
    db.commit()
    db.close()
    assert client.get("/api/me").status_code == 401


def test_root_redirects_by_login_state(client):
    assert client.get("/").headers["Location"].endswith("/login.html")
    register(client)
    login(client)
    assert client.get("/").headers["Location"].endswith("/index.html")
