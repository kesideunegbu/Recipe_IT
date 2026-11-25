import pytest

from app import create_app
from ratelimit import RateLimiter
from test_recipes import make_generator, recipe, reply


class FakeClock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now


@pytest.fixture
def clock():
    return FakeClock()


# --- RateLimiter -------------------------------------------------------------

def test_allows_up_to_the_limit_then_blocks(clock):
    limiter = RateLimiter([(3, 60)], clock=clock)
    assert [limiter.hit("u")[0] for _ in range(3)] == [True, True, True]
    allowed, wait = limiter.hit("u")
    assert not allowed
    assert wait == 60


def test_window_slides(clock):
    limiter = RateLimiter([(2, 60)], clock=clock)
    limiter.hit("u")
    clock.now += 30
    limiter.hit("u")
    clock.now += 10
    assert limiter.hit("u") == (False, 20)     # first hit expires in 20s
    clock.now += 20
    assert limiter.hit("u") == (True, 0)       # first hit has expired
    assert limiter.hit("u")[0] is False        # second and third still count


def test_blocked_attempts_are_not_counted(clock):
    limiter = RateLimiter([(1, 60)], clock=clock)
    limiter.hit("u")
    for _ in range(5):
        clock.now += 10
        assert limiter.hit("u")[0] is False
    clock.now += 10                            # 60s after the only real hit
    assert limiter.hit("u") == (True, 0)


def test_users_are_counted_separately(clock):
    limiter = RateLimiter([(1, 60)], clock=clock)
    assert limiter.hit("alice")[0]
    assert limiter.hit("bob")[0]
    assert not limiter.hit("alice")[0]


def test_daily_cap_applies_after_minute_window(clock):
    limiter = RateLimiter([(2, 60), (3, 86400)], clock=clock)
    limiter.hit("u")
    limiter.hit("u")
    clock.now += 61
    assert limiter.hit("u")[0]                 # 3rd of the day
    clock.now += 61
    allowed, wait = limiter.hit("u")           # minute is clear, day is not
    assert not allowed
    assert wait == 86400 - 122


def test_wait_is_rounded_up_to_whole_seconds(clock):
    limiter = RateLimiter([(1, 60)], clock=clock)
    limiter.hit("u")
    clock.now += 59.6
    assert limiter.hit("u") == (False, 1)


def test_idle_users_are_forgotten(clock):
    limiter = RateLimiter([(5, 60)], clock=clock)
    for i in range(1000):
        limiter.hit(f"old{i}")
    clock.now += 61
    limiter.hit("new")                         # 1001 keys: triggers a sweep
    assert list(limiter._hits) == ["new"]


@pytest.mark.parametrize("rules", [[], [(0, 60)], [(5, 0)]])
def test_rejects_bad_rules(rules):
    with pytest.raises(ValueError):
        RateLimiter(rules)


# --- endpoint ----------------------------------------------------------------

def login(app, email):
    c = app.test_client()
    c.post("/api/register", json={"email": email, "password": "password123"})
    c.post("/api/login", json={"email": email, "password": "password123"})
    return c


@pytest.fixture
def app(tmp_path, monkeypatch, clock):
    monkeypatch.setenv("GENERATE_PER_MINUTE", "2")
    monkeypatch.setenv("GENERATE_PER_DAY", "5")
    app = create_app(database=str(tmp_path / "test.db"), secret_key="test-secret")
    # Same limits as configured, on a clock the test controls.
    app.extensions["generate_limiter"] = RateLimiter(
        [(app.config["GENERATE_PER_MINUTE"], 60), (app.config["GENERATE_PER_DAY"], 86400)],
        clock=clock,
    )
    gen, _ = make_generator(*[reply(recipe()) for _ in range(20)])
    app.extensions["recipe_generator"] = gen
    return app


def generate(client, ingredients=("eggs",)):
    return client.post("/api/recipes/generate", json={"ingredients": list(ingredients)})


def test_endpoint_returns_429_with_retry_after(app):
    c = login(app, "a@example.com")
    assert generate(c).status_code == 200
    assert generate(c).status_code == 200
    res = generate(c)
    assert res.status_code == 429
    assert res.headers["Retry-After"] == "60"
    assert res.get_json()["error"] == "You're making recipes too quickly. Try again in 60 seconds."


def test_endpoint_daily_cap_message_in_hours(app, clock):
    c = login(app, "a@example.com")
    for _ in range(5):
        assert generate(c).status_code == 200
        clock.now += 61
    res = generate(c)
    assert res.status_code == 429
    assert "hours" in res.get_json()["error"]


def test_bad_input_does_not_use_allowance(app):
    c = login(app, "a@example.com")
    for _ in range(5):
        assert generate(c, ingredients=[]).status_code == 400
    assert generate(c).status_code == 200
    assert generate(c).status_code == 200


def test_limit_is_per_user(app):
    alice = login(app, "alice@example.com")
    bob = login(app, "bob@example.com")
    generate(alice)
    generate(alice)
    assert generate(alice).status_code == 429
    assert generate(bob).status_code == 200


def test_limit_configured_from_environment(app):
    assert app.config["GENERATE_PER_MINUTE"] == 2
    assert app.config["GENERATE_PER_DAY"] == 5


@pytest.mark.parametrize("value", ["0", "-1", "ten", "2.5"])
def test_bad_limit_setting_rejected(monkeypatch, tmp_path, value):
    monkeypatch.setenv("GENERATE_PER_MINUTE", value)
    with pytest.raises(ValueError, match="GENERATE_PER_MINUTE"):
        create_app(database=str(tmp_path / "t.db"), secret_key="x")
