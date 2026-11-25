import pytest


@pytest.fixture(autouse=True)
def no_real_gemini(monkeypatch):
    # Backend/.env may hold a real key. Tests must never call Gemini (cost,
    # speed, flakiness), so hide it; tests that need a generator inject a fake.
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
