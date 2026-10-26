"""Edits to a published table are staged in a pending revision; agents read only what is live."""

import pytest
from conftest import make_user
from test_quarantine import T, agent_columns, cols_of, first_sync, resync  # noqa: F401


def published_orders(c, Local, extra_tables=()):
    first_sync(Local, T("orders", ("order_id", "bigint"), ("amount", "double"), ("notes", "varchar")), *extra_tables)
    ids = {x["fqn"].split(".")[1]: x["id"] for x in c.get("/api/tables").json()}
    tid = ids["orders"]
    assert c.patch(f"/api/tables/{tid}", json={"description": "Orders", "grain": "one row per order",
                                               "table_type": "fact", "status": "published"}).status_code == 200
    return tid, ids


def agent_text(c, name="wh.sales.orders"):
    return c.get(f"/agent/tables/{name}/context").text


def pending(c, tid):
    return c.get(f"/api/tables/{tid}/revision").json()


def test_edits_to_a_published_table_are_staged_and_invisible_to_agents(api):
    c, Local = api
    tid, _ = published_orders(c, Local)
    r = c.patch(f"/api/tables/{tid}", json={"description": "Orders v2"}).json()
    assert (r["staged"], r["applied"]) == (1, 0)

    assert "description: Orders\n" in agent_text(c)                       # agents still read the live version
    editor = c.get(f"/api/tables/{tid}").json()
    assert editor["description"] == "Orders v2"                           # ...the editor sees the pending value
    assert editor["pending"]["count"] == 1 and editor["pending"]["table_fields"] == ["description"]
    p = pending(c, tid)
    assert p["diff"] == [{"scope": "table", "column": None, "field": "description", "old": "Orders", "new": "Orders v2"}]
    assert c.get("/api/catalog/tables", params={"pending": True}).json()["total"] == 1
    assert c.get("/api/catalog/tables").json()["items"][0]["pending"] is True


def test_publishing_a_revision_makes_it_live_and_bumps_the_version(api):
    c, Local = api
    tid, _ = published_orders(c, Local)
    assert c.get(f"/api/tables/{tid}").json()["version"] == 1            # published once => version 1
    c.patch(f"/api/tables/{tid}", json={"description": "Orders v2", "owner": "data-team"})

    out = c.post(f"/api/tables/{tid}/revision/publish", json={"message": "Clarify the description"}).json()
    assert out == {"version": 2, "changes": 2}
    assert "description: Orders v2" in agent_text(c)
    assert pending(c, tid)["pending"] is None
    assert ("table.updated", {"table": "wh.sales.orders", "id": tid, "version": 2, "changes": 2}) in c.events

    hist = c.get(f"/api/tables/{tid}/revisions").json()
    assert [h["number"] for h in hist["items"]] == [2, 1] and hist["version"] == 2
    assert hist["items"][0]["message"] == "Clarify the description" and hist["items"][0]["changes"] == 2
    v2 = c.get(f"/api/tables/{tid}/revisions/2").json()
    assert {(d["field"], d["old"], d["new"]) for d in v2["diff"]} == {("description", "Orders", "Orders v2"),
                                                                       ("owner", None, "data-team")}
    assert c.post(f"/api/tables/{tid}/revision/publish", json={}).status_code == 404   # nothing left to publish


def test_discarding_drops_the_pending_changes_only(api):
    c, Local = api
    tid, _ = published_orders(c, Local)
    c.patch(f"/api/tables/{tid}", json={"description": "Nope"})
    assert c.delete(f"/api/tables/{tid}/revision").json() == {"discarded": True}
    assert pending(c, tid)["pending"] is None
    assert c.get(f"/api/tables/{tid}").json()["description"] == "Orders"
    assert c.delete(f"/api/tables/{tid}/revision").status_code == 404


def test_draft_tables_are_edited_directly(api):
    c, Local = api
    first_sync(Local, ("order_id", "bigint"))
    tid = c.get("/api/tables").json()[0]["id"]
    r = c.patch(f"/api/tables/{tid}", json={"description": "Direct"}).json()
    assert (r["staged"], r["applied"]) == (0, 1)
    assert pending(c, tid)["pending"] is None
    assert c.get(f"/api/tables/{tid}/revisions").json()["items"] == []   # no history until it is published


def test_setting_a_field_back_to_its_live_value_withdraws_it(api):
    c, Local = api
    tid, _ = published_orders(c, Local)
    c.patch(f"/api/tables/{tid}", json={"description": "Changed", "owner": "a"})
    c.patch(f"/api/tables/{tid}", json={"description": "Orders"})        # back to live
    assert pending(c, tid)["pending"]["table_fields"] == ["owner"]
    c.patch(f"/api/tables/{tid}", json={"owner": None})
    assert pending(c, tid)["pending"] is None                             # nothing left => the revision disappears


def test_column_edits_are_staged_but_marking_pii_is_immediate(api):
    c, Local = api
    tid, _ = published_orders(c, Local)
    notes = cols_of(c, tid)["notes"]["id"]
    amount = cols_of(c, tid)["amount"]["id"]

    r = c.patch(f"/api/columns/{amount}", json={"description": "Net amount", "role": "measure"}).json()
    assert (r["staged"], r["applied"]) == (2, 0)
    assert "Net amount" not in agent_text(c)
    ed = cols_of(c, tid)["amount"]
    assert ed["description"] == "Net amount" and ed["staged_fields"] == ["description", "role"]

    r = c.patch(f"/api/columns/{notes}", json={"pii": True}).json()       # tightening safety goes live at once
    assert (r["staged"], r["applied"]) == (0, 1)
    assert "pii: true" in agent_text(c)
    r = c.patch(f"/api/columns/{notes}", json={"pii": False}).json()      # loosening it is reviewed like any content
    assert (r["staged"], r["applied"]) == (1, 0)
    assert "pii: true" in agent_text(c)

    c.post(f"/api/tables/{tid}/revision/publish", json={})
    assert "Net amount" in agent_text(c) and "pii: true" not in agent_text(c)


def test_status_and_review_flags_stay_live(api):
    c, Local = api
    tid, _ = published_orders(c, Local)
    r = c.patch(f"/api/tables/{tid}", json={"needs_review": False}).json()
    assert (r["staged"], r["applied"]) == (0, 1)
    assert pending(c, tid)["pending"] is None


def test_unpublishing_folds_pending_changes_in_and_republishing_records_direct_edits(api):
    c, Local = api
    tid, _ = published_orders(c, Local)
    c.patch(f"/api/tables/{tid}", json={"description": "Orders v2"})
    assert c.patch(f"/api/tables/{tid}", json={"status": "draft"}).status_code == 200
    assert pending(c, tid)["pending"] is None                             # nobody reads it now: applied, versioned
    hist = c.get(f"/api/tables/{tid}/revisions").json()["items"]
    assert [h["number"] for h in hist] == [2, 1] and hist[0]["message"] == "Applied when the table was unpublished"
    assert ("table.unpublished", {"table": "wh.sales.orders", "id": tid}) in c.events

    c.patch(f"/api/tables/{tid}", json={"description": "Edited while hidden"})        # draft => direct
    assert c.get(f"/api/tables/{tid}/revisions").json()["version"] == 2
    c.patch(f"/api/tables/{tid}", json={"status": "published"})
    hist = c.get(f"/api/tables/{tid}/revisions").json()
    assert hist["version"] == 3 and "Re-published" in hist["items"][0]["message"]
    c.patch(f"/api/tables/{tid}", json={"status": "draft"})
    c.patch(f"/api/tables/{tid}", json={"status": "published"})            # no content change => no new version
    assert c.get(f"/api/tables/{tid}/revisions").json()["version"] == 3


def test_restoring_a_version_is_staged_and_reviewable(api):
    c, Local = api
    tid, _ = published_orders(c, Local)
    c.patch(f"/api/tables/{tid}", json={"description": "Orders v2"})
    c.post(f"/api/tables/{tid}/revision/publish", json={})                # v2

    preview = c.get(f"/api/tables/{tid}/revisions/1").json()["restore_preview"]
    assert [(d["field"], d["old"], d["new"]) for d in preview] == [("description", "Orders v2", "Orders")]
    r = c.post(f"/api/tables/{tid}/revisions/1/restore", json={}).json()
    assert r == {"staged": 1, "applied": 0, "from_version": 1}
    assert "description: Orders v2" in agent_text(c)                      # not live until someone publishes it
    c.post(f"/api/tables/{tid}/revision/publish", json={})                # v3
    assert "description: Orders\n" in agent_text(c)
    assert c.get(f"/api/tables/{tid}/revisions/3").json()["message"] == "Restore of v1"

    assert c.post(f"/api/tables/{tid}/revisions/3/restore", json={}).status_code == 409      # already matches
    assert c.post(f"/api/tables/{tid}/revisions/99/restore", json={}).status_code == 404
    c.patch(f"/api/tables/{tid}", json={"owner": "x"})
    assert c.post(f"/api/tables/{tid}/revisions/2/restore", json={}).status_code == 409      # pending exists
    assert c.post(f"/api/tables/{tid}/revisions/2/restore", json={"replace": True}).status_code == 200
    assert pending(c, tid)["pending"]["table_fields"] == ["description"]  # the owner edit was replaced


def test_restoring_on_a_draft_applies_immediately(api):
    c, Local = api
    tid, _ = published_orders(c, Local)
    c.patch(f"/api/tables/{tid}", json={"description": "Orders v2"})
    c.post(f"/api/tables/{tid}/revision/publish", json={})
    c.patch(f"/api/tables/{tid}", json={"status": "draft"})
    r = c.post(f"/api/tables/{tid}/revisions/1/restore", json={}).json()
    assert (r["staged"], r["applied"]) == (0, 1)
    assert c.get(f"/api/tables/{tid}").json()["description"] == "Orders"


def test_minimum_documentation_applies_to_the_result_of_a_revision(api):
    c, Local = api
    tid, _ = published_orders(c, Local)                                    # description+grain+type = 3 of 6 parts
    make_user(c, "admin", "boss@example.com")
    c.put("/api/admin/settings", json={"min_completeness_to_publish": 0.4})
    c.patch(f"/api/tables/{tid}", json={"description": None, "grain": None})        # drops it to 1/6
    r = c.post(f"/api/tables/{tid}/revision/publish", json={})
    assert r.status_code == 422 and "would be" in r.json()["detail"]
    assert "description: Orders" in agent_text(c)                         # nothing leaked
    c.patch(f"/api/tables/{tid}", json={"description": "Orders", "grain": "one row per order"})   # back to live
    assert pending(c, tid)["pending"] is None


def test_second_approver_rule_blocks_publishing_your_own_edits(api):
    c, Local = api
    tid, _ = published_orders(c, Local)
    s1 = make_user(c, "steward", "s1@example.com")
    s2 = make_user(c, "steward", "s2@example.com")
    c.put("/api/admin/settings", json={"revision_requires_different_approver": True})

    assert s1.patch(f"/api/tables/{tid}", json={"owner": "team"}).json()["staged"] == 1
    assert s1.post(f"/api/tables/{tid}/revision/publish", json={}).status_code == 403
    assert s2.post(f"/api/tables/{tid}/revision/publish", json={}).status_code == 200
    assert "version" in {a["field"] for a in c.get("/api/admin/audit").json()["items"]}

    s1.patch(f"/api/tables/{tid}", json={"owner": "other"})
    s2.patch(f"/api/tables/{tid}", json={"grain": "g2"})                   # now both contributed
    p = pending(c, tid)["pending"]
    assert set(p["contributors"]) == {"s1@example.com", "s2@example.com"} and p["count"] == 2
    assert s1.post(f"/api/tables/{tid}/revision/publish", json={}).status_code == 403
    assert s2.post(f"/api/tables/{tid}/revision/publish", json={}).status_code == 403
    assert c.post(f"/api/tables/{tid}/revision/publish", json={}).status_code == 200      # a third person may


def test_permissions_viewers_read_but_cannot_stage_or_publish(api):
    c, Local = api
    tid, _ = published_orders(c, Local)
    viewer = make_user(c, "viewer", "v@example.com")
    c.patch(f"/api/tables/{tid}", json={"owner": "x"})
    assert viewer.get(f"/api/tables/{tid}/revision").status_code == 200
    assert viewer.get(f"/api/tables/{tid}/revisions").status_code == 200
    assert viewer.patch(f"/api/tables/{tid}", json={"owner": "y"}).status_code == 403
    assert viewer.post(f"/api/tables/{tid}/revision/publish", json={}).status_code == 403
    assert viewer.delete(f"/api/tables/{tid}/revision").status_code == 403
    assert viewer.post(f"/api/tables/{tid}/revisions/1/restore", json={}).status_code == 403


def test_bulk_edits_stage_for_published_tables_and_apply_to_drafts(api):
    c, Local = api
    tid, ids = published_orders(c, Local, extra_tables=[T("customers", ("customer_id", "bigint"))])
    r = c.post("/api/catalog/tables/bulk-update", json={"filters": {}, "patch": {"owner": "data-team"}}).json()
    assert (r["matched"], r["changed"], r["staged"]) == (2, 1, 1)         # customers (draft) live, orders staged
    q = c.get("/api/catalog/revisions/pending").json()
    assert q["total"] == 1 and q["items"][0]["table"] == "wh.sales.orders" and q["items"][0]["changes"] == 1
    assert c.get("/api/catalog/stats").json()["totals"]["pending"] == 1

    out = c.post("/api/catalog/revisions/bulk", json={"action": "publish", "message": "owner sweep"}).json()
    assert out == {"done": 1, "failed": 0, "failed_examples": []}
    assert c.get("/api/catalog/revisions/pending").json()["total"] == 0
    assert c.get(f"/api/tables/{tid}").json()["owner"] == "data-team"
    assert c.post("/api/catalog/revisions/bulk", json={"action": "bogus"}).status_code == 422


def test_bulk_publish_reports_failures_without_stopping(api):
    c, Local = api
    tid, ids = published_orders(c, Local, extra_tables=[T("customers", ("customer_id", "bigint"))])
    c.patch(f"/api/tables/{ids['customers']}", json={"description": "Customers", "grain": "g", "table_type": "dimension",
                                                     "status": "published"})
    make_user(c, "admin", "boss@example.com")
    for t in (tid, ids["customers"]):
        c.patch(f"/api/tables/{t}", json={"owner": "x"})
    c.put("/api/admin/settings", json={"min_completeness_to_publish": 0.5})
    c.patch(f"/api/tables/{ids['customers']}", json={"description": None, "grain": None})     # this one can't pass
    out = c.post("/api/catalog/revisions/bulk", json={"action": "publish"}).json()
    assert out["done"] == 1 and out["failed"] == 1 and "documented" in out["failed_examples"][0]["reason"]
    assert c.get("/api/catalog/revisions/pending").json()["total"] == 1                         # the failed one stays pending
    out = c.post("/api/catalog/revisions/bulk", json={"action": "discard", "table_ids": [ids["customers"]]}).json()
    assert out["done"] == 1 and c.get("/api/catalog/revisions/pending").json()["total"] == 0


def test_column_dictionary_apply_stages_and_treats_staged_values_as_filled(api):
    c, Local = api
    tid, ids = published_orders(c, Local, extra_tables=[T("customers", ("customer_id", "bigint"), ("order_id", "bigint"))])
    c.patch(f"/api/tables/{ids['customers']}", json={"description": "C", "grain": "g", "table_type": "dimension", "status": "published"})
    r = c.post("/api/catalog/column-groups/apply", json={"name": "order_id", "patch": {"description": "Order key"}}).json()
    assert (r["matched"], r["updated"], r["staged"], r["tables"]) == (2, 2, 2, 2)
    assert "Order key" not in agent_text(c)
    again = c.post("/api/catalog/column-groups/apply", json={"name": "order_id", "patch": {"description": "Other"}}).json()
    assert again["updated"] == 0                                           # a staged value counts as already filled
    forced = c.post("/api/catalog/column-groups/apply", json={"name": "order_id", "only_empty": False,
                                                              "patch": {"description": "Forced"}}).json()
    assert forced["updated"] == 2
    assert c.get("/api/catalog/revisions/pending").json()["total"] == 2
    c.post("/api/catalog/revisions/bulk", json={"action": "publish"})
    assert "description: Forced" in agent_text(c)


def test_csv_import_stages_for_published_tables(api):
    c, Local = api
    tid, _ = published_orders(c, Local)
    body = "source,schema,table,column,description\nwh,sales,orders,amount,Net amount\n".encode()
    r = c.post("/api/catalog/import/columns", content=body).json()
    assert (r["updated"], r["staged"]) == (1, 1) and "Net amount" not in agent_text(c)
    t = "source,schema,table,description\nwh,sales,orders,Orders (csv)\n".encode()
    r = c.post("/api/catalog/import/tables", content=t).json()
    assert r["staged"] == 1 and pending(c, tid)["pending"]["count"] == 2


def test_a_column_dropped_meanwhile_does_not_break_publishing(api):
    c, Local = api
    tid, _ = published_orders(c, Local)
    notes = cols_of(c, tid)["notes"]["id"]
    c.patch(f"/api/columns/{notes}", json={"description": "Free text"})
    c.patch(f"/api/tables/{tid}", json={"owner": "x"})
    resync(Local, T("orders", ("order_id", "bigint"), ("amount", "double")))     # notes dropped from the lake
    r = c.post(f"/api/tables/{tid}/revision/publish", json={})
    assert r.status_code == 200 and c.get(f"/api/tables/{tid}").json()["owner"] == "x"


def test_staged_edits_are_audited_with_who_and_a_staged_flag(api):
    c, Local = api
    tid, _ = published_orders(c, Local)
    s1 = make_user(c, "steward", "s1@example.com")
    s1.patch(f"/api/tables/{tid}", json={"description": "Orders v2"})
    c.post(f"/api/tables/{tid}/revision/publish", json={"message": "m"})
    log = c.get("/api/admin/audit", params={"q": "Orders v2"}).json()["items"]
    staged = [a for a in log if a["field"] == "description"]
    assert staged and staged[0]["staged"] is True and staged[0]["actor"] == "s1@example.com" and staged[0]["old"] == "Orders"
    versions = c.get("/api/admin/audit", params={"q": "v2"}).json()["items"]
    assert any(a["field"] == "version" and a["new"] == "v2" and a["actor"] == "boss@example.com" and not a["staged"]
               for a in versions)


def test_lazy_baseline_for_tables_published_before_this_feature(api):
    c, Local = api
    first_sync(Local, T("orders", ("order_id", "bigint")))
    tid = c.get("/api/tables").json()[0]["id"]
    with Local() as s:                                                     # published the old way: no revision rows
        from app.models import Table
        t = s.get(Table, tid)
        t.status, t.description, t.grain, t.table_type = "published", "Old", "g", "fact"
        s.commit()
    assert c.get(f"/api/tables/{tid}/revisions").json() == {"version": 0, "items": []}
    c.patch(f"/api/tables/{tid}", json={"description": "New"})
    assert c.get(f"/api/tables/{tid}/revisions").json()["version"] == 1   # baseline captured the pre-edit state
    c.post(f"/api/tables/{tid}/revision/publish", json={})
    v1 = c.get(f"/api/tables/{tid}/revisions/1").json()
    assert v1["message"] == "Baseline before staged editing"
    assert c.post(f"/api/tables/{tid}/revisions/1/restore", json={}).json()["staged"] == 1
