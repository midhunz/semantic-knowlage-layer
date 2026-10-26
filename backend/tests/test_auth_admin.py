"""Accounts, roles, API keys, publishing rules, webhooks and audit. Each test gets a fresh database."""

import hashlib
import hmac
import json
import threading
import time
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest
from fastapi.testclient import TestClient
from conftest import fresh_engine
from sqlalchemy.orm import sessionmaker

import app.auth as auth
import app.mcp_server as mcp_server
import app.services.webhooks as webhooks
from app.connectors.base import ColumnMeta, TableMeta
from app.db import get_session
from app.main import app
from app.models import ApiKey, Source
from app.services.sync import apply_sync

PW = "correct horse battery"


@pytest.fixture
def env(monkeypatch):
    engine = fresh_engine()
    Local = sessionmaker(bind=engine, expire_on_commit=False)

    def override():
        with Local() as s:
            yield s

    app.dependency_overrides[get_session] = override
    monkeypatch.setattr(webhooks, "SessionLocal", Local)
    monkeypatch.setattr(mcp_server, "SessionLocal", Local)
    yield TestClient(app), Local
    app.dependency_overrides.clear()


def seed(Local):
    """Source 'wh' with finance.invoices and sales.orders."""
    with Local() as s:
        src = Source(name="wh", config={})
        s.add(src)
        s.commit()
        apply_sync(s, src, [
            TableMeta("fin", "invoices", [ColumnMeta("id", "bigint"), ColumnMeta("email", "varchar")]),
            TableMeta("crm", "orders", [ColumnMeta("id", "bigint")]),
        ])
        for t in src.tables:
            t.domain = "finance" if t.name == "invoices" else "sales"
            t.description = "d"
            t.grain = "one row per x"
            t.table_type = "fact"
        src.tables[0].columns[1].pii = True
        for t in src.tables:        # these tests are not about quarantine: release anything the sync held back
            for col in t.columns:
                col.quarantined, col.quarantine_reason = False, None
        s.commit()
        return {t.name: t.id for t in src.tables}


def admin_client(env_):
    c, Local = env_
    r = c.post("/api/auth/setup", json={"email": "Boss@Example.com", "name": "Boss", "password": PW})
    assert r.status_code == 200 and r.json()["role"] == "admin" and r.json()["email"] == "boss@example.com"
    return c


def new_user(c, role, email=None):
    email = email or f"{role}@example.com"
    r = c.post("/api/admin/users", json={"email": email, "role": role, "password": PW})
    assert r.status_code == 200, r.text
    other = TestClient(app)
    assert other.post("/api/auth/login", json={"email": email, "password": PW}).status_code == 200
    return other


# ----------------------------------------------------------------------------- open mode & setup
def test_open_mode_until_first_admin_then_login_is_required(env):
    c, Local = env
    ids = seed(Local)
    assert c.get("/api/auth/me").json() == {"auth_required": False, "setup_needed": True, "needs_cli_setup": False, "user": None,
                                                "org_name": ""}
    assert c.get("/api/tables").status_code == 200          # open, as before accounts existed
    assert c.get("/api/admin/settings").status_code == 200   # anonymous acts as admin in open mode
    assert c.post("/api/admin/users", json={"email": "a@b.co", "role": "viewer"}).status_code == 409

    admin_client(env)
    anon = TestClient(app)
    assert anon.get("/health").status_code == 200
    for path in ("/api/tables", "/agent/search?q=x", "/api/admin/settings", "/api/catalog/stats"):
        assert anon.get(path).status_code == 401, path
    assert c.get("/api/auth/me").json()["user"]["email"] == "boss@example.com"
    assert c.post("/api/auth/setup", json={"email": "x@y.zz", "password": PW}).status_code == 409
    assert ids and c.get(f"/api/tables/{ids['invoices']}").status_code == 200


def test_login_logout_throttle_and_password_change(env):
    c = admin_client(env)
    other = TestClient(app)
    assert other.post("/api/auth/login", json={"email": "boss@example.com", "password": "nope"}).status_code == 401
    assert other.post("/api/auth/login", json={"email": "boss@example.com", "password": PW}).status_code == 200
    assert other.get("/api/tables").status_code == 200
    other.post("/api/auth/logout")
    assert other.get("/api/tables").status_code == 401

    for _ in range(5):
        other.post("/api/auth/login", json={"email": "boss@example.com", "password": "bad"})
    assert other.post("/api/auth/login", json={"email": "boss@example.com", "password": PW}).status_code == 429

    assert c.post("/api/auth/change-password", json={"current": "wrong", "new": "x" * 10}).status_code == 400
    assert c.post("/api/auth/change-password", json={"current": PW, "new": "short"}).status_code == 422
    assert c.post("/api/auth/change-password", json={"current": PW, "new": "a brand new password"}).status_code == 200


# ----------------------------------------------------------------------------- roles
def test_roles_viewer_read_only_steward_edits_admin_manages(env):
    c, Local = env
    ids = seed(Local)
    admin_client(env)
    viewer, steward = new_user(c, "viewer"), new_user(c, "steward")
    tid = ids["orders"]

    assert viewer.get(f"/api/tables/{tid}").status_code == 200
    assert viewer.patch(f"/api/tables/{tid}", json={"owner": "x"}).status_code == 403
    assert steward.patch(f"/api/tables/{tid}", json={"owner": "data-team"}).status_code == 200
    for who in (viewer, steward):
        assert who.get("/api/admin/settings").status_code == 403
        assert who.post("/api/admin/keys", json={"name": "k"}).status_code == 403
    assert viewer.get("/agent/search?q=orders").status_code == 200  # people can preview agent output

    log = c.get("/api/admin/audit").json()["items"]
    assert any(i["actor"] == "steward@example.com" and i["field"] == "owner" and i["target"] == "wh.crm.orders"
               for i in log)


def test_last_admin_cannot_be_removed_and_deactivation_signs_out(env):
    c = admin_client(env)
    me = c.get("/api/auth/me").json()["user"]["id"]
    assert c.patch(f"/api/admin/users/{me}", json={"role": "steward"}).status_code == 409
    assert c.patch(f"/api/admin/users/{me}", json={"is_active": False}).status_code == 409
    assert c.delete(f"/api/admin/users/{me}").status_code == 409

    victim = new_user(c, "steward")
    uid = next(u["id"] for u in c.get("/api/admin/users").json() if u["email"] == "steward@example.com")
    assert victim.get("/api/tables").status_code == 200
    c.patch(f"/api/admin/users/{uid}", json={"is_active": False})
    assert victim.get("/api/tables").status_code == 401
    assert TestClient(app).post("/api/auth/login", json={"email": "steward@example.com", "password": PW}).status_code == 401

    # a second admin makes demoting the first legal
    c.post("/api/admin/users", json={"email": "two@example.com", "role": "admin", "password": PW})
    assert c.patch(f"/api/admin/users/{me}", json={"role": "steward"}).status_code == 200


def test_temp_password_flow_and_reset_signs_out(env):
    c = admin_client(env)
    made = c.post("/api/admin/users", json={"email": "new@example.com", "role": "viewer"}).json()
    temp = made["temporary_password"]
    assert temp and made["user"]["must_change_password"]
    u = TestClient(app)
    assert u.post("/api/auth/login", json={"email": "new@example.com", "password": temp}).status_code == 200
    assert u.get("/api/tables").status_code == 200
    reset = c.post(f"/api/admin/users/{made['user']['id']}/reset-password").json()
    assert reset["temporary_password"] != temp
    assert u.get("/api/tables").status_code == 401
    assert c.post("/api/admin/users", json={"email": "NEW@example.com", "role": "viewer"}).status_code == 409


# ----------------------------------------------------------------------------- api keys
def test_api_key_lifecycle_scopes_and_secret_shown_once(env):
    c, Local = env
    seed(Local)
    admin_client(env)
    made = c.post("/api/admin/keys", json={"name": "Support bot", "scopes": ["agent:read"]}).json()
    secret, kid = made["secret"], made["key"]["id"]
    assert secret.startswith("sl_live_") and made["key"]["prefix"] == secret[:15]
    listing = json.dumps(c.get("/api/admin/keys").json())
    assert secret not in listing and "key_hash" not in listing
    with Local() as s:  # only a hash is stored
        assert s.get(ApiKey, kid).key_hash == hashlib.sha256(secret.encode()).hexdigest()

    bot = TestClient(app)
    h = {"X-API-Key": secret}
    assert bot.get("/agent/search?q=x", headers=h).status_code == 200
    assert bot.get("/agent/search?q=x", headers={"Authorization": f"Bearer {secret}"}).status_code == 200
    assert bot.get("/api/tables", headers=h).status_code == 403           # agent scope only
    assert bot.get("/api/admin/settings", headers=h).status_code == 403    # keys never reach admin
    assert bot.get("/agent/search?q=x", headers={"X-API-Key": "sl_live_wrong"}).status_code == 401
    k = next(k for k in c.get("/api/admin/keys").json() if k["id"] == kid)
    assert k["use_count"] >= 2 and k["last_used_at"]

    rotated = c.post(f"/api/admin/keys/{kid}/rotate").json()
    assert bot.get("/agent/search?q=x", headers=h).status_code == 401      # old secret dead
    assert bot.get("/agent/search?q=x", headers={"X-API-Key": rotated["secret"]}).status_code == 200

    c.post(f"/api/admin/keys/{kid}/revoke")
    assert bot.get("/agent/search?q=x", headers={"X-API-Key": rotated["secret"]}).status_code == 401
    assert next(k for k in c.get("/api/admin/keys").json() if k["id"] == kid)["status"] == "revoked"
    assert c.delete(f"/api/admin/keys/{kid}").status_code == 200

    assert c.post("/api/admin/keys", json={"name": "x", "scopes": ["root"]}).status_code == 422
    assert c.post("/api/admin/keys", json={"name": "x", "scopes": []}).status_code == 422


def test_key_expiry_and_catalog_scopes(env):
    c, Local = env
    ids = seed(Local)
    admin_client(env)
    rw = c.post("/api/admin/keys", json={"name": "ci", "scopes": ["catalog:write"]}).json()
    ro = c.post("/api/admin/keys", json={"name": "report", "scopes": ["catalog:read"]}).json()
    ex = c.post("/api/admin/keys", json={"name": "temp", "scopes": ["agent:read"], "expires_in_days": 1}).json()
    bot, tid = TestClient(app), ids["orders"]

    assert bot.patch(f"/api/tables/{tid}", json={"owner": "ci"}, headers={"X-API-Key": rw["secret"]}).status_code == 200
    assert bot.get(f"/api/tables/{tid}", headers={"X-API-Key": ro["secret"]}).status_code == 200
    assert bot.patch(f"/api/tables/{tid}", json={"owner": "x"}, headers={"X-API-Key": ro["secret"]}).status_code == 403
    assert any(i["actor"] == "key:ci" for i in c.get("/api/admin/audit").json()["items"])

    with Local() as s:
        s.get(ApiKey, ex["key"]["id"]).expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
        s.commit()
    assert bot.get("/agent/search?q=x", headers={"X-API-Key": ex["secret"]}).status_code == 401


def test_domain_restricted_key_only_sees_its_domains(env):
    c, Local = env
    seed(Local)
    admin_client(env)
    c.post("/api/catalog/tables/bulk-update", json={"filters": {}, "patch": {"status": "published"}})
    key = c.post("/api/admin/keys", json={"name": "fin", "allowed_domains": ["finance"]}).json()["secret"]
    bot, h = TestClient(app), {"X-API-Key": key}

    hits = bot.get("/agent/search?q=id", headers=h).json()
    assert [x["table"] for x in hits] == ["wh.fin.invoices"]
    assert bot.get("/agent/tables/wh.fin.invoices/context", headers=h).status_code == 200
    assert bot.get("/agent/tables/wh.crm.orders/context", headers=h).status_code == 404
    export = bot.get("/agent/export", headers=h).text
    assert "invoices" in export and "orders" not in export
    full = c.get("/agent/export").text  # an unrestricted person sees both
    assert "invoices" in full and "orders" in full


# ----------------------------------------------------------------------------- settings & policy
def test_agent_defaults_and_pii_exclusion_apply_without_params(env):
    c, Local = env
    ids = seed(Local)
    admin_client(env)
    c.patch(f"/api/tables/{ids['invoices']}", json={"description_ar": "الفواتير", "status": "published"})
    assert "email" in c.get("/agent/tables/wh.fin.invoices/context").text      # name visible by default

    assert c.put("/api/admin/settings", json={"pii_columns_in_agent_output": "exclude",
                                              "default_lang": "ar", "org_name": "ICP"}).status_code == 200
    ctx = c.get("/agent/tables/wh.fin.invoices/context").text
    assert "email" not in ctx and "الفواتير" in ctx                           # PII column hidden, Arabic by default
    assert "الفواتير" not in c.get("/agent/tables/wh.fin.invoices/context?lang=en").text
    assert c.get("/api/auth/me").json()["org_name"] == "ICP"
    assert c.put("/api/admin/settings", json={"default_lang": "fr"}).status_code == 422
    assert c.put("/api/admin/settings", json={"min_completeness_to_publish": 2}).status_code == 422

    assert "الفواتير" in mcp_server.describe_table("wh.fin.invoices")          # MCP honours the same defaults


def test_publishing_rules_block_single_and_bulk_publish(env):
    c, Local = env
    ids = seed(Local)
    admin_client(env)
    c.put("/api/admin/settings", json={"require_review_before_publish": True})
    r = c.patch(f"/api/tables/{ids['orders']}", json={"status": "published"})
    assert r.status_code == 422 and "reviewed" in r.json()["detail"]
    assert c.patch(f"/api/tables/{ids['orders']}", json={"status": "reviewed"}).status_code == 200
    assert c.patch(f"/api/tables/{ids['orders']}", json={"status": "published"}).status_code == 200

    c.put("/api/admin/settings", json={"require_review_before_publish": False, "min_completeness_to_publish": 0.99})
    r = c.patch(f"/api/tables/{ids['invoices']}", json={"status": "published"})
    assert r.status_code == 422 and "documented" in r.json()["detail"]
    res = c.post("/api/catalog/tables/bulk-update", json={"ids": [ids["invoices"]], "patch": {"status": "published"}}).json()
    assert res["changed"] == 0 and res["blocked"] == 1 and "documented" in res["blocked_examples"][0]["reason"]


# ----------------------------------------------------------------------------- webhooks
class _Receiver:
    def __init__(self):
        self.hits = []
        outer = self

        class H(BaseHTTPRequestHandler):
            def do_POST(self):
                body = self.rfile.read(int(self.headers["Content-Length"]))
                outer.hits.append((dict(self.headers), body))
                self.send_response(204)
                self.end_headers()

            def log_message(self, *a):
                pass

        self.server = HTTPServer(("127.0.0.1", 0), H)
        self.url = f"http://127.0.0.1:{self.server.server_port}/hook"
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def wait(self, n, timeout=5):
        end = time.time() + timeout
        while len(self.hits) < n and time.time() < end:
            time.sleep(0.05)
        return self.hits

    def close(self):
        self.server.shutdown()


def test_webhooks_signed_test_ping_and_publish_event(env):
    c, Local = env
    ids = seed(Local)
    admin_client(env)
    rx = _Receiver()
    try:
        assert c.post("/api/admin/webhooks", json={"name": "x", "url": "ftp://nope", "events": ["table.published"]}).status_code == 422
        assert c.post("/api/admin/webhooks", json={"name": "x", "url": rx.url, "events": ["bogus"]}).status_code == 422
        made = c.post("/api/admin/webhooks", json={"name": "cache", "url": rx.url,
                                                   "events": ["table.published", "table.unpublished"]}).json()
        secret, hid = made["secret"], made["webhook"]["id"]
        assert secret not in json.dumps(c.get("/api/admin/webhooks").json())

        t = c.post(f"/api/admin/webhooks/{hid}/test").json()
        assert t["ok"] and t["status"].startswith("2")
        headers, body = rx.wait(1)[0]
        headers = {k.lower(): v for k, v in headers.items()}  # urllib re-cases header names
        want = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
        assert headers["x-sl-signature"] == want and headers["x-sl-event"] == "webhook.test"

        c.patch(f"/api/tables/{ids['orders']}", json={"status": "published"})
        hits = rx.wait(2)
        assert len(hits) == 2 and json.loads(hits[1][1])["event"] == "table.published"
        assert json.loads(hits[1][1])["data"]["table"] == "wh.crm.orders"

        c.patch(f"/api/tables/{ids['orders']}", json={"status": "draft"})
        assert json.loads(rx.wait(3)[2][1])["event"] == "table.unpublished"

        c.patch(f"/api/admin/webhooks/{hid}", json={"is_active": False})
        c.patch(f"/api/tables/{ids['orders']}", json={"status": "published"})
        time.sleep(0.4)
        assert len(rx.hits) == 3                                              # paused hooks stay quiet
        assert c.get("/api/admin/webhooks").json()[0]["last_status"]
    finally:
        rx.close()


def test_webhook_delivery_failure_is_reported_not_raised(env):
    c, _ = env
    admin_client(env)
    hid = c.post("/api/admin/webhooks", json={"name": "dead", "url": "http://127.0.0.1:9/x",
                                              "events": ["catalog.synced"]}).json()["webhook"]["id"]
    r = c.post(f"/api/admin/webhooks/{hid}/test").json()
    assert r["ok"] is False and r["status"].startswith("failed")


def test_audit_filters_and_pagination(env):
    c, Local = env
    ids = seed(Local)
    admin_client(env)
    for i in range(5):
        c.patch(f"/api/tables/{ids['orders']}", json={"owner": f"team{i}"})
    page = c.get("/api/admin/audit", params={"page_size": 2}).json()
    assert page["total"] >= 5 and len(page["items"]) == 2 and "boss@example.com" in page["actors"]
    assert c.get("/api/admin/audit", params={"q": "team3"}).json()["total"] == 2  # set to team3, then replaced
    assert c.get("/api/admin/audit", params={"actor": "nobody"}).json()["total"] == 0


def test_bulk_update_empty_ids_touches_nothing_but_empty_filters_means_all(env):
    c, Local = env
    seed(Local)
    admin_client(env)
    nothing = c.post("/api/catalog/tables/bulk-update", json={"ids": [], "patch": {"owner": "x"}}).json()
    assert nothing == {"matched": 0, "changed": 0, "staged": 0, "blocked": 0, "blocked_examples": []}
    everything = c.post("/api/catalog/tables/bulk-update", json={"filters": {}, "patch": {"owner": "y"}}).json()
    assert everything["matched"] == 2 and everything["changed"] == 2
    assert c.post("/api/catalog/tables/bulk-update", json={"patch": {"owner": "z"}}).status_code == 400
