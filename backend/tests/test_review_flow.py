"""draft → review → published for dimensions, metrics and glossary terms; live content never changes before approval."""

from conftest import go_live, make_user
from test_dimensions import create_person_category, resolve, values_of


def post(c, kind, i, action, **body):
    return c.post(f"/api/review/{kind}/{i}/{action}", json=body or None)


def test_new_content_starts_as_a_draft_and_is_invisible_to_agents(api):
    c, _ = api
    did = create_person_category(c, publish=False)
    mid = c.post("/api/metrics", json={"name": "Headcount", "sql_expression": "SUM(headcount)", "status": "published"}).json()
    gid = c.post("/api/glossary", json={"term": "Resident", "definition": "Lives here", "synonyms": ["expat"]}).json()
    assert c.get(f"/api/dimensions/{did}").json()["status"] == "draft"
    assert mid["status"] == "draft" and gid["status"] == "draft"                       # a client cannot publish directly
    assert c.get("/agent/dimensions").json() == []
    assert c.get("/agent/glossary/resolve", params={"term": "expat"}).json() == []
    assert c.get("/agent/search", params={"q": "Headcount"}).json() == []

    for kind, i in (("dimension", did), ("metric", mid["id"]), ("glossary", gid["id"])):
        assert post(c, kind, i, "submit").json()["status"] == "review"
    queue = c.get("/api/review").json()
    assert queue["total"] == 3 and {x["kind"] for x in queue["items"]} == {"dimension", "metric", "glossary"}
    assert c.get("/agent/dimensions").json() == []                                       # review is still not live

    for kind, i in (("dimension", did), ("metric", mid["id"]), ("glossary", gid["id"])):
        assert post(c, kind, i, "approve").json()["status"] == "published"
    assert [d["key"] for d in c.get("/agent/dimensions").json()] == ["person_category"]
    assert c.get("/agent/glossary/resolve", params={"term": "expat"}).json()[0]["term"] == "Resident"
    assert c.get("/api/review").json()["total"] == 0


def test_rejecting_sends_it_back_with_a_note_and_editing_during_review_returns_it_to_draft(api):
    c, _ = api
    gid = c.post("/api/glossary", json={"term": "Resident", "definition": "x"}).json()["id"]
    assert post(c, "glossary", gid, "approve").status_code == 409                       # not submitted yet
    post(c, "glossary", gid, "submit")
    assert post(c, "glossary", gid, "reject", note=" ").status_code == 422              # a reason is required
    r = post(c, "glossary", gid, "reject", note="Definition is too vague").json()
    assert r["status"] == "draft" and r["review_note"] == "Definition is too vague"
    post(c, "glossary", gid, "submit")
    c.put(f"/api/glossary/{gid}", json={"term": "Resident", "definition": "Better"})
    assert c.get(f"/api/glossary/{gid}").json()["status"] == "draft"                    # editing pulls it out of review
    assert c.get("/api/review").json()["total"] == 0


def test_editing_a_live_item_goes_through_a_draft_copy_and_agents_keep_the_live_version(api):
    c, _ = api
    did = create_person_category(c)
    mid = c.post("/api/metrics", json={"name": "Headcount", "sql_expression": "SUM(a)"}).json()["id"]
    go_live(c, "metric", mid)
    c.events.clear()

    assert c.post(f"/api/dimensions/{did}/values", json={"value": "ALIEN"}).status_code == 409   # live is read-only
    assert c.put(f"/api/metrics/{mid}", json={"name": "Headcount", "sql_expression": "SUM(b)"}).status_code == 409

    copy = post(c, "dimension", did, "edit-draft").json()
    assert copy["id"] != did and copy["live_id"] == did and post(c, "dimension", did, "edit-draft").json()["id"] == copy["id"]
    c.post(f"/api/dimensions/{copy['id']}/values", json={"value": "ALIEN", "aliases": ["martians"]})
    c.patch(f"/api/dimensions/{copy['id']}", json={"label": "Category"})
    mcopy = post(c, "metric", mid, "edit-draft").json()
    c.put(f"/api/metrics/{mcopy['id']}", json={"name": "Headcount", "sql_expression": "SUM(b)"})

    assert [d["key"] for d in c.get("/api/dimensions").json()] == ["person_category"]       # copies are not listed
    assert c.get("/api/dimensions").json()[0]["draft_id"] == copy["id"]
    live = c.get("/agent/dimensions/person_category").json()
    assert live["label"] == "Person category" and "ALIEN" not in [v["value"] for v in live["values"]]
    assert values_of(resolve(c, "martians")) == []
    assert [m["name"] for m in c.get("/agent/metrics").json()] == ["Headcount"]           # one metric, the live one
    assert not c.events                                                                  # nothing announced yet

    post(c, "dimension", copy["id"], "submit")
    post(c, "metric", mcopy["id"], "submit")
    diff = {x["kind"]: x for x in c.get("/api/review").json()["items"]}
    assert diff["dimension"]["live_id"] == did and diff["dimension"]["diff"]["values"]["added"] == ["ALIEN"]
    assert [f["field"] for f in diff["dimension"]["diff"]["fields"]] == ["label"]
    assert diff["metric"]["diff"]["fields"] == [{"field": "sql_expression", "old": "SUM(a)", "new": "SUM(b)"}]

    assert post(c, "dimension", copy["id"], "approve").json()["id"] == did                # the live row, not the copy
    post(c, "metric", mcopy["id"], "approve")
    new = c.get("/agent/dimensions/person_category").json()
    assert new["label"] == "Category" and "ALIEN" in [v["value"] for v in new["values"]]
    assert values_of(resolve(c, "martians")) == ["ALIEN"]
    assert [e[0] for e in c.events] == ["dimension.updated", "metric.updated"]
    assert c.get(f"/api/dimensions/{copy['id']}").status_code == 404                     # the copy is gone
    assert c.get("/api/dimensions").json()[0]["draft_id"] is None


def test_rejected_or_discarded_copies_leave_the_live_version_alone(api):
    c, _ = api
    did = create_person_category(c)
    copy = post(c, "dimension", did, "edit-draft").json()["id"]
    c.post(f"/api/dimensions/{copy}/values", json={"value": "ALIEN"})
    post(c, "dimension", copy, "submit")
    r = post(c, "dimension", copy, "reject", note="Not a real category").json()
    assert r["status"] == "draft" and r["review_note"] == "Not a real category"
    assert len(c.get("/agent/dimensions/person_category").json()["values"]) == 4
    assert c.delete(f"/api/review/dimension/{copy}/draft").status_code == 200
    assert c.get(f"/api/dimensions/{copy}").status_code == 404
    assert c.delete(f"/api/review/dimension/{did}/draft").status_code == 409              # a live item is not a draft copy
    again = post(c, "dimension", did, "edit-draft").json()["id"]                          # a new copy starts from live
    assert len(c.get(f"/api/dimensions/{again}").json()["values_list"]) == 4


def test_the_same_key_can_exist_as_live_and_copy_and_columns_stay_unique(api):
    from test_dimensions import lake

    c, Local = api
    tables, cols = lake(Local, c)
    pop = cols[("population", "person_category")]
    did = create_person_category(c, bind=[pop])
    assert c.post("/api/dimensions", json={"key": "person_category"}).status_code == 409
    copy = post(c, "dimension", did, "edit-draft").json()["id"]
    assert len(c.get(f"/api/dimensions/{copy}").json()["bindings_list"]) == 1             # the copy carries the bindings
    other = c.post("/api/dimensions", json={"key": "other"}).json()["id"]
    assert c.post(f"/api/dimensions/{other}/bindings", json={"column_ids": [pop]}).status_code == 409
    assert c.post(f"/api/dimensions/{copy}/bindings", json={"column_ids": [pop]}).status_code == 200   # its own column: fine
    found = c.get("/api/dimensions/columns", params={"q": "person_category"}).json()
    assert {f["bound_to"] for f in found if f["id"] == pop} == {"person_category"}
    assert c.delete(f"/api/dimensions/{did}").status_code == 200                           # deleting the live one drops the copy
    assert c.get(f"/api/dimensions/{copy}").status_code == 404


def test_roles_unpublish_and_second_approver(api):
    c, _ = api
    steward = make_user(c, "steward", "s@example.com")
    viewer = make_user(c, "viewer", "v@example.com")
    gid = steward.post("/api/glossary", json={"term": "Resident", "definition": "x"}).json()["id"]
    assert post(viewer, "glossary", gid, "submit").status_code == 403
    assert viewer.get("/api/review").status_code == 200
    post(steward, "glossary", gid, "submit")
    assert c.put("/api/admin/settings", json={"revision_requires_different_approver": True}).status_code == 200
    r = post(steward, "glossary", gid, "approve")
    assert r.status_code == 403 and "different steward" in r.json()["detail"]             # the submitter cannot approve alone
    assert post(c, "glossary", gid, "approve").status_code == 200
    assert post(c, "glossary", gid, "unpublish").json()["status"] == "draft"
    assert c.get("/agent/glossary/resolve", params={"term": "resident"}).json() == []
