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
    app = create_app(database=str(tmp_path / "test.db"))
    return app.test_client()


def register(client, username="alice", password="password123"):
    return client.post("/api/register", json={"username": username, "password": password})


def login(client, username="alice", password="password123"):
    return client.post("/api/login", json={"username": username, "password": password})


def test_register_then_login(client):
    assert register(client).status_code == 201
    assert login(client).status_code == 200


def test_login_wrong_password(client):
    register(client)
    assert login(client, password="wrongpass1").status_code == 401


def test_login_unknown_user_gives_same_error(client):
    register(client)
    unknown = login(client, username="bob")
    wrong = login(client, password="wrongpass1")
    assert unknown.status_code == wrong.status_code == 401
    assert unknown.get_json() == wrong.get_json()


def test_duplicate_username_rejected(client):
    register(client)
    assert register(client, username="ALICE").status_code == 409


def test_register_rejects_weak_password(client):
    assert register(client, password="short").status_code == 400


def test_password_stored_as_hash(client, tmp_path):
    import sqlite3

    register(client)
    row = sqlite3.connect(tmp_path / "test.db").execute(
        "SELECT password_hash FROM users WHERE username = 'alice'"
    ).fetchone()
    assert row[0].startswith("$argon2id$")
    assert "password123" not in row[0]
