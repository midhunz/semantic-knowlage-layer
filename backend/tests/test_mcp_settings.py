"""MCP connector settings: the tool list is read from the server, switches are enforced per call, run_query is capped."""

import pytest
from conftest import make_user

import app.mcp_server as mcp_server


@pytest.fixture
def admin(api, monkeypatch):
    client, Local = api
    monkeypatch.setattr(mcp_server, "SessionLocal", Local)
    make_user(client, "admin")
    return client


def test_info_lists_the_real_tools_and_flags_raw_data_access(admin):
    r = admin.get("/api/admin/mcp")
    assert r.status_code == 200
    info = r.json()
    names = {t["name"] for t in info["tools"]}
    assert {"list_tables", "describe_table", "list_metrics", "run_query"} <= names
    assert {t["name"]: t["access"] for t in info["tools"]}["run_query"] == "raw"
    assert {t["name"]: t["access"] for t in info["tools"]}["list_tables"] == "catalog"
    assert all(t["summary"] for t in info["tools"])
    assert info["server"]["transport"] == "stdio"
    assert info["settings"] == {"mcp_enabled": True, "mcp_disabled_tools": [], "mcp_run_query_max_rows": 1000}


def test_unknown_tool_and_out_of_range_rows_are_rejected(admin):
    assert admin.put("/api/admin/settings", json={"mcp_disabled_tools": ["drop_everything"]}).status_code == 422
    assert admin.put("/api/admin/settings", json={"mcp_run_query_max_rows": 0}).status_code == 422
    assert admin.put("/api/admin/settings", json={"mcp_run_query_max_rows": 5000}).status_code == 422
    assert admin.get("/api/admin/mcp").json()["settings"]["mcp_disabled_tools"] == []


def test_a_disabled_tool_is_refused_at_call_time_and_others_still_work(admin):
    assert admin.put("/api/admin/settings", json={"mcp_disabled_tools": ["run_query"]}).status_code == 200
    with pytest.raises(ValueError, match="turned off by an administrator"):
        mcp_server.run_query("select 1")
    assert mcp_server.list_tables() == []  # unaffected
    admin.put("/api/admin/settings", json={"mcp_disabled_tools": []})
    with pytest.raises(ValueError, match="No data source"):  # allowed again: it now fails only for lack of a source
        mcp_server.run_query("select 1")


def test_master_switch_turns_every_tool_off(admin):
    admin.put("/api/admin/settings", json={"mcp_enabled": False})
    for call in (mcp_server.list_tables, mcp_server.list_metrics, mcp_server.get_sample_queries):
        with pytest.raises(ValueError, match="MCP access is turned off"):
            call()
    admin.put("/api/admin/settings", json={"mcp_enabled": True})
    assert mcp_server.list_tables() == []


def test_run_query_rows_are_capped_by_the_setting(admin, monkeypatch):
    from app.models import Source

    seen = {}

    class Conn:
        def run_query(self, sql, max_rows):
            seen["rows"] = max_rows
            return {"rows": []}

    with mcp_server.SessionLocal() as s:
        s.add(Source(name="lake", kind="trino", config={}))
        s.commit()
    monkeypatch.setattr(mcp_server, "get_connector", lambda kind, config: Conn())
    admin.put("/api/admin/settings", json={"mcp_run_query_max_rows": 50})
    mcp_server.run_query("select 1", max_rows=800)
    assert seen["rows"] == 50
    mcp_server.run_query("select 1", max_rows=10)
    assert seen["rows"] == 10


def test_only_admins_can_read_or_change_it(api):
    client, _ = api
    make_user(client, "admin")
    viewer = make_user(client, "viewer")
    assert viewer.get("/api/admin/mcp").status_code in (401, 403)
    assert viewer.put("/api/admin/settings", json={"mcp_enabled": False}).status_code in (401, 403)
