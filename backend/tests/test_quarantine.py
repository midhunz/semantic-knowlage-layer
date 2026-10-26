"""New or sensitive-looking columns stay hidden from agents until a steward releases them."""

from conftest import make_user

from app.connectors.base import ColumnMeta, TableMeta
from app.models import Source
from app.services.sync import apply_sync


def T(table, *cols, schema="sales"):
    """One lake table: T("orders", ("order_id", "bigint"), ...)"""
    return TableMeta(schema, table, [ColumnMeta(n, t, True, i) for i, (n, t) in enumerate(cols, start=1)], "iceberg")


def _tables(args):
    return list(args) if args and isinstance(args[0], TableMeta) else [T("orders", *args)]


def first_sync(Local, *args):
    """Sync the whole lake as `args` describes it: either columns of sales.orders, or T(...) tables."""
    with Local() as s:
        src = s.query(Source).filter_by(name="wh").first() or Source(name="wh", config={})
        s.add(src)
        s.commit()
        return apply_sync(s, src, _tables(args))


def resync(Local, *args):
    with Local() as s:
        return apply_sync(s, s.query(Source).filter_by(name="wh").one(), _tables(args))


def cols_of(c, tid):
    return {x["name"]: x for x in c.get(f"/api/tables/{tid}").json()["columns"]}


def agent_columns(c, name="wh.sales.orders"):
    text = c.get(f"/agent/tables/{name}/context").text
    return [line.split(": ", 1)[1] for line in text.splitlines() if line.strip().startswith("- name:")]


def publish(c, tid):
    assert c.patch(f"/api/tables/{tid}", json={"description": "d", "grain": "g", "table_type": "fact",
                                               "status": "published"}).status_code == 200


def test_sensitive_names_are_quarantined_even_on_a_brand_new_table(api):
    c, Local = api
    stats = first_sync(Local, ("order_id", "bigint"), ("customer_email", "varchar"), ("net_amount", "double"))
    assert stats["columns_quarantined"] == 1
    tid = c.get("/api/tables").json()[0]["id"]
    cols = cols_of(c, tid)
    assert cols["customer_email"]["quarantined"] and "sensitive (email)" in cols["customer_email"]["quarantine_reason"]
    assert not cols["order_id"]["quarantined"] and not cols["net_amount"]["quarantined"]

    publish(c, tid)
    assert agent_columns(c) == ["order_id", "net_amount"]                       # the email column is not exposed


def test_new_column_on_a_published_table_is_hidden_until_released(api):
    c, Local = api
    first_sync(Local, ("order_id", "bigint"), ("amount", "double"))
    tid = c.get("/api/tables").json()[0]["id"]
    publish(c, tid)
    assert agent_columns(c) == ["order_id", "amount"]

    stats = resync(Local, ("order_id", "bigint"), ("amount", "double"), ("channel", "varchar"), ("national_id", "varchar"))
    assert stats["columns_added"] == 2 and stats["columns_quarantined"] == 2
    assert agent_columns(c) == ["order_id", "amount"]                           # nothing new reaches agents
    assert c.get("/agent/search", params={"q": "channel"}).json() == []         # ...nor search
    cols = cols_of(c, tid)
    assert cols["channel"]["quarantine_reason"] == "New column"
    assert cols["national_id"]["quarantine_reason"] == "New column; name looks sensitive (national_id)"
    assert c.get(f"/api/tables/{tid}").json()["quarantined_count"] == 2

    assert c.patch(f"/api/columns/{cols['channel']['id']}", json={"quarantined": False}).status_code == 200
    assert agent_columns(c) == ["order_id", "amount", "channel"]
    assert cols_of(c, tid)["channel"]["quarantine_reason"] is None


def test_release_can_flag_pii_and_the_pii_setting_then_hides_it(api):
    c, Local = api
    first_sync(Local, ("order_id", "bigint"))
    tid = c.get("/api/tables").json()[0]["id"]
    publish(c, tid)
    make_user(c, "admin", "boss@example.com")
    resync(Local, ("order_id", "bigint"), ("phone", "varchar"))
    q = c.get("/api/catalog/quarantine").json()
    assert q["total"] == 1 and q["items"][0]["column"] == "phone"

    r = c.post("/api/catalog/quarantine/release", json={"ids": [q["items"][0]["id"]], "mark_pii": True}).json()
    assert r == {"released": 1, "marked_pii": 1}
    assert cols_of(c, tid)["phone"]["pii"] is True
    assert "phone" in agent_columns(c)                                           # released: name visible, values masked
    c.put("/api/admin/settings", json={"pii_columns_in_agent_output": "exclude"})
    assert "phone" not in agent_columns(c)


def test_name_patterns_are_configurable_by_admins(api):
    c, Local = api
    make_user(c, "admin", "boss@example.com")
    assert c.put("/api/admin/settings", json={"pii_name_patterns": "loyalty_code, vip"}).status_code == 200
    first_sync(Local, ("customer_email", "varchar"), ("loyalty_code", "varchar"), ("vip_flag", "boolean"))
    tid = c.get("/api/tables").json()[0]["id"]
    q = cols_of(c, tid)
    assert not q["customer_email"]["quarantined"]                               # no longer in the pattern list
    assert q["loyalty_code"]["quarantined"] and q["vip_flag"]["quarantined"]


def test_quarantine_queue_filters_bulk_release_and_stats(api):
    c, Local = api
    first_sync(Local, T("a", ("id", "bigint")), T("b", ("id", "bigint"), schema="hr"))
    resync(Local, T("a", ("id", "bigint"), ("x1", "varchar"), ("x2", "varchar")),
           T("b", ("id", "bigint"), ("salary", "double"), schema="hr"))
    q = c.get("/api/catalog/quarantine").json()
    assert q["total"] == 3
    assert c.get("/api/catalog/quarantine", params={"schema": "hr"}).json()["total"] == 1
    assert c.get("/api/catalog/quarantine", params={"reason": "sensitive"}).json()["total"] == 1
    assert c.get("/api/catalog/quarantine", params={"q": "x2"}).json()["total"] == 1
    assert c.get("/api/catalog/stats").json()["totals"]["quarantined_columns"] == 3
    assert c.get("/api/catalog/tables", params={"quarantined": True}).json()["total"] == 2

    r = c.post("/api/catalog/quarantine/release", json={"filters": {"reason": "new"}}).json()
    assert r["released"] == 3                                                    # "New column" ones, incl. the salary one
    assert c.get("/api/catalog/quarantine").json()["total"] == 0
    assert c.post("/api/catalog/quarantine/release", json={}).status_code == 400


def test_joins_never_reveal_a_hidden_column(api):
    c, Local = api
    first_sync(Local, T("orders", ("order_id", "bigint"), ("customer_id", "bigint")), T("customers", ("customer_id", "bigint")))
    t = {x["fqn"].split(".")[1]: x["id"] for x in c.get("/api/tables").json()}
    for name in t:
        c.patch(f"/api/tables/{t[name]}", json={"description": "d", "grain": "g", "table_type": "fact", "status": "published"})
    a = cols_of(c, t["orders"])["customer_id"]["id"]
    b = cols_of(c, t["customers"])["customer_id"]["id"]
    assert c.post("/api/relationships", json={"from_column_id": a, "to_column_id": b}).status_code == 200
    assert "relationships" in c.get("/agent/tables/wh.sales.orders/context").text

    c.patch(f"/api/columns/{b}", json={"quarantined": True})                    # hide one end of the join
    assert "relationships" not in c.get("/agent/tables/wh.sales.orders/context").text
    assert "customers" not in c.get("/agent/tables/wh.sales.orders/context").text


def test_manual_hold_reappearing_and_dropped_columns(api):
    c, Local = api
    first_sync(Local, ("order_id", "bigint"), ("amount", "double"))
    tid = c.get("/api/tables").json()[0]["id"]
    publish(c, tid)
    amount = cols_of(c, tid)["amount"]["id"]
    c.patch(f"/api/columns/{amount}", json={"quarantined": True})
    assert cols_of(c, tid)["amount"]["quarantine_reason"] == "Held by anonymous"   # open mode actor
    assert agent_columns(c) == ["order_id"]
    c.patch(f"/api/columns/{amount}", json={"quarantined": False})

    resync(Local, ("order_id", "bigint"))                                         # amount dropped from the lake
    resync(Local, ("order_id", "bigint"), ("amount", "double"))                   # ...and comes back
    assert not cols_of(c, tid)["amount"]["quarantined"]                           # it was reviewed before: not re-held
    assert agent_columns(c) == ["order_id", "amount"]
    resync(Local, ("order_id", "bigint"), ("secret_note", "varchar"))             # held for review...
    assert c.get("/api/catalog/quarantine").json()["total"] == 1
    resync(Local, ("order_id", "bigint"))                                         # ...then dropped from the lake
    assert c.get("/api/catalog/quarantine").json()["total"] == 0                  # a dropped column is not queued


def test_draft_tables_keep_their_first_sync_columns_visible_after_publishing(api):
    c, Local = api
    first_sync(Local, ("order_id", "bigint"), ("amount", "double"))
    tid = c.get("/api/tables").json()[0]["id"]
    assert all(not v["quarantined"] for v in cols_of(c, tid).values())            # publishing a table = reviewing its columns
