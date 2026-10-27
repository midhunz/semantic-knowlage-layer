import os

# Never touch the developer's real catalog DB from tests. These must be set before `app` is imported.
# Run the whole suite against Postgres with:  SL_TEST_DATABASE_URL=postgresql://user:pass@host/db pytest
TEST_URL = os.environ.get("SL_TEST_DATABASE_URL")
os.environ["SL_DATABASE_URL"] = TEST_URL or "sqlite://"
os.environ["SL_ENV"] = "development"
for var in ("SL_REQUIRE_AUTH", "SL_COOKIE_SECURE", "SL_STATIC_DIR", "SL_CORS_ORIGINS"):
    os.environ.pop(var, None)


def fresh_engine():
    """An engine on a clean, fully created schema (in-memory SQLite, or the Postgres test database)."""
    from app.db import Base, make_engine
    import app.models  # noqa: F401

    eng = make_engine(TEST_URL or "sqlite://")
    Base.metadata.drop_all(eng)
    Base.metadata.create_all(eng)
    return eng


import pytest  # noqa: E402

PW = "correct horse battery"


@pytest.fixture
def api(monkeypatch):
    """(client, sessionmaker) on a fresh database, with outbound webhooks captured instead of sent."""
    from fastapi.testclient import TestClient
    from sqlalchemy.orm import sessionmaker

    from app.db import get_session
    from app.main import app
    from app.services import webhooks

    engine = fresh_engine()
    Local = sessionmaker(bind=engine, expire_on_commit=False)

    def override():
        with Local() as s:
            yield s

    sent = []
    app.dependency_overrides[get_session] = override
    monkeypatch.setattr(webhooks, "emit", lambda session, event, payload: sent.append((event, payload)) or 0)
    client = TestClient(app)
    client.events = sent
    yield client, Local
    app.dependency_overrides.clear()


def make_user(client, role, email=None):
    """Sign in as a new user of `role` (the first call on a fresh DB creates the admin)."""
    from fastapi.testclient import TestClient

    from app.main import app

    email = email or f"{role}@example.com"
    if client.get("/api/auth/me").json()["setup_needed"]:
        assert client.post("/api/auth/setup", json={"email": "boss@example.com", "name": "Boss", "password": PW}).status_code == 200
    if role != "admin" or email != "boss@example.com":
        assert client.post("/api/admin/users", json={"email": email, "role": role, "password": PW}).status_code == 200
    other = TestClient(app)
    other.events = client.events
    assert other.post("/api/auth/login", json={"email": email, "password": PW}).status_code == 200
    return other


def go_live(c, kind, item_id):
    """Submit a draft for review and approve it (what a steward and a reviewer do together)."""
    assert c.post(f"/api/review/{kind}/{item_id}/submit").status_code == 200
    r = c.post(f"/api/review/{kind}/{item_id}/approve")
    assert r.status_code == 200, r.text
    return r.json()
