"""Production hardening: migrations, config guards, cookies, headers, throttle, CLI, static UI."""

from datetime import datetime, timedelta, timezone

import pytest
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.runtime.migration import MigrationContext
from conftest import TEST_URL, fresh_engine
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import inspect, select, text
from sqlalchemy.orm import sessionmaker

import app.cli as cli
import app.migrate as mig
import app.web as web
from app.config import Settings, settings, validate_for_production
from app.db import Base, get_session, make_engine, normalize_url
from app.main import app
from app.models import LoginAttempt, Source, User, UserSession

PW = "correct horse battery"


def blank_engine(tmp_path):
    """An engine on a completely empty database (no tables, no alembic_version)."""
    eng = make_engine(TEST_URL or f"sqlite:///{tmp_path / 'm.db'}")
    Base.metadata.drop_all(eng)
    with eng.begin() as c:
        c.execute(text("DROP TABLE IF EXISTS alembic_version"))
    return eng


@pytest.fixture
def env(monkeypatch):
    engine = fresh_engine()
    Local = sessionmaker(bind=engine, expire_on_commit=False)

    def override():
        with Local() as s:
            yield s

    app.dependency_overrides[get_session] = override
    monkeypatch.setattr(cli, "SessionLocal", Local)
    monkeypatch.setattr(web, "SessionLocal", Local)
    yield TestClient(app), Local, engine
    app.dependency_overrides.clear()


# ----------------------------------------------------------------------------- migrations
def test_migrations_build_exactly_the_schema_the_models_describe(tmp_path):
    eng = blank_engine(tmp_path)
    assert mig.current_revision(eng) is None
    assert "upgraded empty ->" in mig.migrate(eng)
    assert mig.current_revision(eng) == mig.head_revision()
    assert {"table", "column", "app_user", "api_key", "login_attempt", "webhook"} <= set(inspect(eng).get_table_names())
    with eng.connect() as c:
        diff = compare_metadata(MigrationContext.configure(c, opts={"compare_type": False}), Base.metadata)
    assert diff == [], f"models and migrations disagree: {diff}"      # fails when someone forgets a migration
    assert mig.migrate(eng).startswith("already at")                   # idempotent


def test_downgrade_then_upgrade_round_trips(tmp_path):
    eng = blank_engine(tmp_path)
    mig.migrate(eng)
    cfg = mig.alembic_config()
    with eng.connect() as conn:
        cfg.attributes["connection"] = conn
        command.downgrade(cfg, "base")
    assert "source" not in inspect(eng).get_table_names()
    mig.upgrade(eng)
    assert "source" in inspect(eng).get_table_names()


def test_pre_migration_database_is_adopted_without_losing_data(tmp_path):
    eng = blank_engine(tmp_path)
    Base.metadata.create_all(eng)                                      # how the app used to build databases
    Local = sessionmaker(bind=eng)
    with Local() as s:
        s.add(Source(name="old", config={}))
        s.commit()
    with eng.begin() as c:                                             # simulate an older release: fewer objects
        c.execute(text('DROP TABLE login_attempt'))
        c.execute(text('ALTER TABLE "table" DROP COLUMN display_name_ar'))
    assert mig.is_legacy(eng)
    with pytest.raises(RuntimeError, match="python -m app.cli migrate"):
        mig.ensure_schema_current(auto=False, eng=eng)                 # production refuses to guess

    assert mig.migrate(eng).startswith("adopted")
    assert mig.current_revision(eng) == mig.head_revision()
    assert "login_attempt" in inspect(eng).get_table_names()
    assert "display_name_ar" in {c["name"] for c in inspect(eng).get_columns("table")}
    with Local() as s:
        assert s.scalar(select(Source.name)) == "old"                  # data untouched


def test_production_startup_refuses_an_outdated_schema(tmp_path):
    eng = blank_engine(tmp_path)
    with pytest.raises(RuntimeError, match="needs"):
        mig.ensure_schema_current(auto=False, eng=eng)
    assert mig.ensure_schema_current(auto=True, eng=eng).startswith("upgraded")
    assert mig.ensure_schema_current(auto=False, eng=eng).startswith("schema at")


# ----------------------------------------------------------------------------- configuration guards
def test_production_config_guards():
    pg = "postgresql://u:p@db/x"
    with pytest.raises(RuntimeError, match="SQLite"):
        validate_for_production(Settings(env="production", database_url="sqlite:///x.db"))
    assert validate_for_production(Settings(env="production", database_url="sqlite:///x.db",
                                            allow_sqlite_in_production=True)) == []
    with pytest.raises(RuntimeError, match="COOKIE_SECURE"):
        validate_for_production(Settings(env="production", database_url=pg, cookie_secure="never"))
    with pytest.raises(RuntimeError, match="REQUIRE_AUTH"):
        validate_for_production(Settings(env="production", database_url=pg, require_auth=False))
    prod = Settings(env="production", database_url=pg)
    assert prod.require_auth is True and prod.cors_origin_list == [] and validate_for_production(prod) == []
    dev = Settings(env="development", database_url="sqlite:///x.db")
    assert dev.require_auth is False and dev.cors_origin_list           # dev keeps its zero-config ergonomics
    assert validate_for_production(dev) == []
    assert validate_for_production(Settings(env="production", database_url=pg, cors_origins="http://localhost:5173")) \
        == ["SL_CORS_ORIGINS allows localhost origins in production."]


def test_postgres_urls_are_normalised_to_the_psycopg_driver():
    assert normalize_url("postgres://u:p@h/d") == "postgresql+psycopg://u:p@h/d"
    assert normalize_url("postgresql://u:p@h/d") == "postgresql+psycopg://u:p@h/d"
    assert normalize_url("postgresql+psycopg://u:p@h/d") == "postgresql+psycopg://u:p@h/d"
    assert normalize_url("sqlite:///x.db") == "sqlite:///x.db"


# ----------------------------------------------------------------------------- cookies, headers, errors
def _setup(c):
    return c.post("/api/auth/setup", json={"email": "a@example.com", "name": "A", "password": PW})


def test_session_cookie_flags_follow_the_scheme_and_setting(env, monkeypatch):
    c, Local, engine = env
    r = _setup(TestClient(app, base_url="http://testserver"))
    cookie = r.headers["set-cookie"].lower()
    assert "httponly" in cookie and "samesite=lax" in cookie and "secure" not in cookie.replace("httponly", "")

    with Local() as s:                                                 # second login attempt over https
        s.query(UserSession).delete()
        s.commit()
    r = TestClient(app, base_url="https://testserver").post("/api/auth/login", json={"email": "a@example.com", "password": PW})
    assert "secure" in r.headers["set-cookie"].lower()                 # auto: https => Secure

    monkeypatch.setattr(settings, "cookie_secure", "always")
    r = TestClient(app, base_url="http://testserver").post("/api/auth/login", json={"email": "a@example.com", "password": PW})
    assert "secure" in r.headers["set-cookie"].lower()
    monkeypatch.setattr(settings, "cookie_secure", "never")
    r = TestClient(app, base_url="https://testserver").post("/api/auth/login", json={"email": "a@example.com", "password": PW})
    assert "; secure" not in r.headers["set-cookie"].lower()


def test_security_headers_request_ids_and_hsts(env):
    c, _, _ = env
    r = c.get("/api/auth/me", headers={"X-Request-ID": "abc123"})
    h = r.headers
    assert h["x-request-id"] == "abc123" and h["x-content-type-options"] == "nosniff" and h["x-frame-options"] == "DENY"
    assert "frame-ancestors 'none'" in h["content-security-policy"] and h["cache-control"] == "no-store"
    assert "strict-transport-security" not in h                        # only meaningful over https
    https = TestClient(app, base_url="https://testserver").get("/api/auth/me")
    assert "max-age=31536000" in https.headers["strict-transport-security"]
    assert len(c.get("/health").headers["x-request-id"]) == 12


def test_unhandled_errors_return_a_request_id_not_a_stack_trace(env):
    c, _, _ = env

    @app.get("/api/_boom_test")
    def boom():
        raise ValueError("secret internal detail")

    try:
        r = TestClient(app, raise_server_exceptions=False).get("/api/_boom_test")
    finally:
        app.router.routes[:] = [rt for rt in app.router.routes if getattr(rt, "path", "") != "/api/_boom_test"]
    assert r.status_code == 500 and r.json()["detail"] == "Internal server error"
    assert "secret internal detail" not in r.text and r.json()["request_id"] == r.headers["x-request-id"]


def test_ready_reports_database_and_schema_state(env, monkeypatch, tmp_path):
    c, _, _ = env
    unmigrated = blank_engine(tmp_path)
    monkeypatch.setattr(web, "default_engine", unmigrated)
    monkeypatch.setattr(mig, "default_engine", unmigrated)
    r = c.get("/ready")
    assert r.status_code == 503 and "run migrations" in r.json()["detail"]
    mig.migrate(unmigrated)
    assert c.get("/ready").json() == {"ready": True, "schema": mig.head_revision()}
    assert c.get("/health").json() == {"ok": True}                     # liveness never touches the database


# ----------------------------------------------------------------------------- authentication in production
def test_production_has_no_anonymous_mode_and_no_browser_setup(env, monkeypatch):
    c, _, _ = env
    monkeypatch.setattr(settings, "require_auth", True)
    me = c.get("/api/auth/me").json()
    assert me["auth_required"] and me["needs_cli_setup"] and not me["setup_needed"]
    for path in ("/api/tables", "/api/admin/settings", "/agent/search?q=x", "/api/catalog/stats"):
        assert c.get(path).status_code == 401, path
    r = _setup(c)
    assert r.status_code == 403 and "create-admin" in r.json()["detail"]
    assert c.get("/health").status_code == 200

    assert cli.main(["create-admin", "--email", "Ops@Example.com", "--password", PW]) == 0
    assert c.post("/api/auth/login", json={"email": "ops@example.com", "password": PW}).status_code == 200
    assert c.get("/api/tables").status_code == 200 and not c.get("/api/auth/me").json()["needs_cli_setup"]


def test_failed_logins_are_throttled_in_the_database_not_in_process_memory(env):
    c, Local, _ = env
    _setup(c)
    for _ in range(5):
        assert TestClient(app).post("/api/auth/login", json={"email": "a@example.com", "password": "bad"}).status_code == 401
    other_worker = TestClient(app)                                     # no shared Python state with the above
    assert other_worker.post("/api/auth/login", json={"email": "a@example.com", "password": PW}).status_code == 429
    with Local() as s:                                                 # the window passes
        for a in s.scalars(select(LoginAttempt)):
            a.at = datetime.now(timezone.utc) - timedelta(seconds=settings.login_window_seconds + 5)
        s.commit()
    assert other_worker.post("/api/auth/login", json={"email": "a@example.com", "password": PW}).status_code == 200
    with Local() as s:                                                 # success clears the record
        assert s.query(LoginAttempt).count() == 0


def test_expired_sessions_are_purged_and_not_honoured(env):
    c, Local, _ = env
    _setup(c)
    assert c.get("/api/tables").status_code == 200
    with Local() as s:
        s.query(UserSession).update({"expires_at": datetime.now(timezone.utc) - timedelta(minutes=1)})
        s.commit()
    assert c.get("/api/tables").status_code == 401
    from app.auth import purge_expired
    with Local() as s:
        purge_expired(s)
        assert s.query(UserSession).count() == 0


def test_bootstrap_admin_from_environment_is_idempotent(env, monkeypatch):
    c, Local, _ = env
    monkeypatch.setattr(settings, "bootstrap_admin_email", "Boot@Example.com")
    monkeypatch.setattr(settings, "bootstrap_admin_password", PW)
    web._bootstrap_admin()
    web._bootstrap_admin()
    with Local() as s:
        assert [u.email for u in s.scalars(select(User))] == ["boot@example.com"]
    assert c.post("/api/auth/login", json={"email": "boot@example.com", "password": PW}).status_code == 200


# ----------------------------------------------------------------------------- CLI
def test_cli_admin_lifecycle(env, capsys):
    c, Local, _ = env
    assert cli.main(["create-admin", "--email", "Root@Example.com", "--name", "Root", "--password", PW]) == 0
    with pytest.raises(SystemExit, match="already exists"):
        cli.main(["create-admin", "--email", "root@example.com", "--password", PW])
    with pytest.raises(SystemExit, match="at least"):
        cli.main(["create-admin", "--email", "x@example.com", "--password", "short"])

    assert c.post("/api/auth/login", json={"email": "root@example.com", "password": PW}).status_code == 200
    capsys.readouterr()
    assert cli.main(["reset-password", "--email", "root@example.com"]) == 0
    out = capsys.readouterr().out
    temp = out.split("sign-in): ")[1].strip()
    assert c.get("/api/tables").status_code == 401                     # old session ended
    r = TestClient(app).post("/api/auth/login", json={"email": "root@example.com", "password": temp})
    assert r.status_code == 200 and r.json()["must_change_password"] is True

    assert cli.main(["reset-password", "--email", "root@example.com", "--password", "my chosen password"]) == 0
    with Local() as s:
        assert s.scalar(select(User.must_change_password)) is False     # a password you chose is not "temporary"
    with pytest.raises(SystemExit, match="No user"):
        cli.main(["reset-password", "--email", "ghost@example.com"])


def test_cli_check_and_sqlite_backup(tmp_path, monkeypatch, capsys):
    if TEST_URL:
        pytest.skip("sqlite-only command")
    import sqlite3
    path = tmp_path / "live.db"
    eng = make_engine(f"sqlite:///{path}")
    mig.migrate(eng)
    with eng.begin() as c:
        c.execute(text("INSERT INTO source (name, kind, config) VALUES ('s', 'trino', '{}')"))
    monkeypatch.setattr(cli, "default_engine", eng)
    monkeypatch.setattr(settings, "database_url", f"sqlite:///{path}")
    assert cli.main(["backup", "--out", str(tmp_path / "bk")]) == 0
    copy = next((tmp_path / "bk").glob("semantic_layer-*.db"))
    assert sqlite3.connect(copy).execute("select name from source").fetchall() == [("s",)]

    monkeypatch.setattr(mig, "default_engine", eng)
    monkeypatch.setattr(cli, "SessionLocal", sessionmaker(bind=eng))
    assert cli.main(["check"]) == 0
    assert "up to date" in capsys.readouterr().out


# ----------------------------------------------------------------------------- serving the built UI
def test_single_container_ui_serving(tmp_path, monkeypatch):
    (tmp_path / "assets").mkdir()
    (tmp_path / "index.html").write_text("<html>APP SHELL</html>")
    (tmp_path / "assets" / "app-1a2b3c.js").write_text("console.log(1)")
    (tmp_path / "vendor").mkdir()
    (tmp_path / "vendor" / "logo.png").write_bytes(b"PNG")
    monkeypatch.setattr(settings, "static_dir", str(tmp_path))
    ui = FastAPI()

    @ui.get("/api/ping")
    def ping():
        return {"pong": True}

    assert web.serve_ui(ui) is True
    c = TestClient(ui)
    assert c.get("/api/ping").json() == {"pong": True}
    assert "APP SHELL" in c.get("/").text and "APP SHELL" in c.get("/catalog").text        # client-side routes
    assert c.get("/catalog").headers["cache-control"] == "no-cache"
    js = c.get("/assets/app-1a2b3c.js")
    assert js.status_code == 200 and "immutable" in js.headers["cache-control"]
    assert c.get("/vendor/logo.png").content == b"PNG"
    r = c.get("/api/does-not-exist")
    assert r.status_code == 404 and "APP SHELL" not in r.text                               # API 404s stay JSON
    assert c.get("/agent/nope").status_code == 404
    esc = c.get("/%2e%2e/%2e%2e/etc/passwd")
    assert "root:" not in esc.text                                                          # no path traversal
    monkeypatch.setattr(settings, "static_dir", str(tmp_path / "missing"))
    assert web.serve_ui(FastAPI()) is False
