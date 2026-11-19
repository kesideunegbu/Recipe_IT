import pytest

from app import create_app
from config import DEFAULT_GEMINI_MODEL, load_config


def test_secret_key_from_environment(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "from-env")
    assert load_config()["SECRET_KEY"] == "from-env"


def test_missing_secret_key_warns_and_uses_random_key(monkeypatch):
    monkeypatch.delenv("SECRET_KEY", raising=False)
    with pytest.warns(UserWarning, match="SECRET_KEY"):
        first = load_config()["SECRET_KEY"]
    with pytest.warns(UserWarning):
        second = load_config()["SECRET_KEY"]
    assert first and first != second


def test_gemini_settings(monkeypatch):
    monkeypatch.delenv("GEMINI_MODEL", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    config = load_config(secret_key="x")
    assert config["GEMINI_MODEL"] == DEFAULT_GEMINI_MODEL
    assert config["GEMINI_API_KEY"] is None

    monkeypatch.setenv("GEMINI_MODEL", "some-other-model")
    monkeypatch.setenv("GEMINI_API_KEY", "abc")
    config = load_config(secret_key="x")
    assert config["GEMINI_MODEL"] == "some-other-model"
    assert config["GEMINI_API_KEY"] == "abc"


def test_fast_gemini_defaults(monkeypatch):
    for name in ["GEMINI_MODEL", "GEMINI_FALLBACK_MODEL", "GEMINI_THINKING_LEVEL", "GEMINI_TIMEOUT_SECONDS"]:
        monkeypatch.delenv(name, raising=False)
    config = load_config(secret_key="x")
    assert config["GEMINI_MODEL"] == "gemini-3.5-flash-lite"
    assert config["GEMINI_FALLBACK_MODEL"] == "gemini-3.6-flash"
    assert config["GEMINI_THINKING_LEVEL"] == "minimal"
    assert config["GEMINI_TIMEOUT_SECONDS"] == 30


@pytest.mark.parametrize("value", ["abc", "0", "-5"])
def test_bad_timeout_rejected(monkeypatch, value):
    monkeypatch.setenv("GEMINI_TIMEOUT_SECONDS", value)
    with pytest.raises(ValueError, match="GEMINI_TIMEOUT_SECONDS"):
        load_config(secret_key="x")


def test_secure_cookie_flag(monkeypatch):
    monkeypatch.delenv("SESSION_COOKIE_SECURE", raising=False)
    assert load_config(secret_key="x")["SESSION_COOKIE_SECURE"] is False
    monkeypatch.setenv("SESSION_COOKIE_SECURE", "1")
    assert load_config(secret_key="x")["SESSION_COOKIE_SECURE"] is True


def test_gemini_key_never_served(tmp_path, monkeypatch):
    # The frontend folder is served as static files; .env lives in Backend/
    # and must not be reachable from the browser.
    monkeypatch.setenv("GEMINI_API_KEY", "super-secret-key")
    client = create_app(database=str(tmp_path / "t.db"), secret_key="x").test_client()
    for path in ["/.env", "/../Backend/.env", "/config.py", "/%2e%2e/Backend/.env"]:
        response = client.get(path)
        assert b"super-secret-key" not in response.data
