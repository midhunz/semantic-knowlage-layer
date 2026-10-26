"""Dimensions: vocabulary, aliases, families, "applies to", bindings, loading values, agent lookup."""

import pytest
from conftest import make_user
from test_quarantine import T, first_sync

import app.mcp_server as mcp_server
from app.models import Dimension, DimensionBinding

# The dimension as authored in the existing semantic layer: person_category.
PERSON = {
    "CITIZEN": ("Citizen", "مواطن", ["citizens", "citizen", "nationals", "emiratis", "مواطن", "مواطنون", "مواطنين"]),
    "EXPAT": ("Expat", "مقيم", ["resident", "residents", "expat", "expats", "expatriates", "مقيم", "مقيمون",
                                 "مقيمين", "وافد", "وافدون"]),
    "GCC": ("GCC national", "مجلس دول التعاون الخليجي", ["gulf nationals", "gcc nationals", "خليجي", "خليجيون",
                                                        "مجلس دول التعاون الخليجي"]),
    "VISITOR": ("Visitor", "زائر", ["visitor", "visitors", "tourists", "زائر", "زوار", "سائح", "سياح"]),
}


def create_person_category(c, publish=True, bind=()):
    r = c.post("/api/dimensions", json={
        "key": "person_category", "label": "Person category", "label_ar": "فئة الشخص",
        "description": "Which population group the row counts: CITIZEN, EXPAT, GCC or VISITOR. “Residents” means EXPAT.",
        "description_ar": "فئة السكان: مواطن، مقيم، مواطنو دول مجلس التعاون الخليجي، أو زائر.",
        "synonyms": ["category"], "synonyms_ar": ["فئة", "الفئة"]})
    assert r.status_code == 200, r.text
    did = r.json()["id"]
    out = c.post(f"/api/dimensions/{did}/values/bulk", json={"values": [
        {"value": v, "label": en, "label_ar": ar, "aliases": al} for v, (en, ar, al) in PERSON.items()]}).json()
    assert out["added"] == 4
    if bind:
        assert c.post(f"/api/dimensions/{did}/bindings", json={"column_ids": list(bind)}).status_code == 200
    if publish:
        assert c.patch(f"/api/dimensions/{did}", json={"status": "published"}).status_code == 200
    return did


def lake(Local, c, publish=True):
    """population(person_category, headcount) and nationality(person_category, nationality)."""
    first_sync(Local, T("population", ("person_category", "varchar"), ("headcount", "bigint")),
               T("nationality", ("person_category", "varchar"), ("nationality", "varchar")),
               T("employees", ("category", "varchar"), schema="hr"))
    tables = {x["fqn"].split(".")[1]: x["id"] for x in c.get("/api/tables").json()}
    cols = {}
    for name, tid in tables.items():
        for col in c.get(f"/api/tables/{tid}").json()["columns"]:
            cols[(name, col["name"])] = col["id"]
        domain = "hr" if name == "employees" else "sales"
        if publish:
            assert c.patch(f"/api/tables/{tid}", json={"description": "d", "grain": "g", "table_type": "fact",
                                                       "domain": domain, "status": "published"}).status_code == 200
    return tables, cols


def resolve(c, text, **params):
    return c.get("/agent/resolve-value", params={"text": text, **params}).json()


def values_of(r):
    return sorted({m["value"] for m in r["matches"]})


# ----------------------------------------------------------------------------- authoring
def test_create_validates_the_key_and_cleans_synonyms(api):
    c, _ = api
    assert c.post("/api/dimensions", json={"key": "Person Category"}).status_code == 422
    assert c.post("/api/dimensions", json={"key": "1abc"}).status_code == 422
    r = c.post("/api/dimensions", json={"key": "region", "synonyms": [" area ", "AREA", "", "zone"]}).json()
    assert r["synonyms"] == ["area", "zone"] and r["status"] == "draft"
    assert c.post("/api/dimensions", json={"key": "region"}).status_code == 409
    c.post("/api/dimensions", json={"key": "gender", "label_ar": "الجنس"})
    assert [d["key"] for d in c.get("/api/dimensions").json()] == ["gender", "region"]
    assert [d["key"] for d in c.get("/api/dimensions", params={"q": "زون"}).json()] == []
    assert [d["key"] for d in c.get("/api/dimensions", params={"q": "الجنس"}).json()] == ["gender"]


def test_the_person_category_dimension_authored_in_full(api):
    c, _ = api
    did = create_person_category(c)
    d = c.get(f"/api/dimensions/{did}").json()
    assert [v["value"] for v in d["values_list"]] == ["CITIZEN", "EXPAT", "GCC", "VISITOR"]
    assert sum(len(v["aliases"]) for v in d["values_list"]) == 7 + 10 + 5 + 7        # as in the spec
    assert d["synonyms_ar"] == ["فئة", "الفئة"] and d["label_ar"] == "فئة الشخص" and d["issues"] == []

    # what people say -> what is stored, in both languages
    for said, stored in [("residents", "EXPAT"), ("Citizens", "CITIZEN"), ("expatriates", "EXPAT"), ("tourists", "VISITOR"),
                         ("gulf nationals", "GCC"), ("مقيمين", "EXPAT"), ("وافدون", "EXPAT"), ("خليجي", "GCC"),
                         ("زوار", "VISITOR"), ("emiratis", "CITIZEN"), ("  RESIDENTS  ", "EXPAT"), ("residents?", "EXPAT")]:
        r = resolve(c, said)
        assert values_of(r) == [stored] and not r["ambiguous"], said
        assert r["matches"][0]["dimension"] == "person_category"
    assert values_of(resolve(c, "مُقيمُون")) == ["EXPAT"]                            # diacritics are ignored
    assert values_of(resolve(c, "EXPAT")) == ["EXPAT"] and resolve(c, "EXPAT")["matches"][0]["via"] == "value"
    assert resolve(c, "martians")["matches"] == []
    assert resolve(c, "residents", dimension="person_category")["matches"][0]["value"] == "EXPAT"
    assert resolve(c, "residents", dimension="other")["matches"] == []

    named = resolve(c, "الفئة")                                                      # the word names the dimension itself
    assert named["dimensions"] == [{"dimension": "person_category", "label": "Person category"}] and named["matches"] == []
    assert resolve(c, "category")["dimensions"][0]["dimension"] == "person_category"


def test_value_crud_the_stored_value_is_immutable(api):
    c, _ = api
    did = c.post("/api/dimensions", json={"key": "status"}).json()["id"]
    d = c.post(f"/api/dimensions/{did}/values", json={"value": "ACTIVE", "label": "Active", "aliases": ["live", "Live", " on "]}).json()
    v = d["values_list"][0]
    assert v["aliases"] == ["live", "on"] and v["position"] == 0
    assert c.post(f"/api/dimensions/{did}/values", json={"value": "ACTIVE"}).status_code == 409
    assert c.post(f"/api/dimensions/{did}/values", json={"value": "  "}).status_code == 422
    d = c.patch(f"/api/dimensions/{did}/values/{v['id']}", json={"label_ar": "نشط", "aliases": ["running"], "value": "HACK"}).json()
    assert d["values_list"][0]["value"] == "ACTIVE" and d["values_list"][0]["aliases"] == ["running"]
    out = c.post(f"/api/dimensions/{did}/values/bulk", json={"values": [{"value": "ACTIVE"}, {"value": "CLOSED"}]}).json()
    assert (out["added"], out["skipped"]) == (1, 1)
    assert c.delete(f"/api/dimensions/{did}/values/{v['id']}").status_code == 409        # it has an alias: confirm first
    assert c.delete(f"/api/dimensions/{did}/values/{v['id']}", params={"confirm": True}).status_code == 200
    assert [x["value"] for x in c.get(f"/api/dimensions/{did}").json()["values_list"]] == ["CLOSED"]
    assert c.delete(f"/api/dimensions/{did}/values/9999").status_code == 404


def test_ambiguous_words_are_warned_about_and_flagged_when_resolving(api):
    c, _ = api
    did = create_person_category(c)
    vid = {v["value"]: v["id"] for v in c.get(f"/api/dimensions/{did}").json()["values_list"]}
    c.patch(f"/api/dimensions/{did}/values/{vid['GCC']}", json={"aliases": ["resident", "gulf nationals"]})
    issues = c.get(f"/api/dimensions/{did}/validation").json()["issues"]
    amb = [i for i in issues if i["code"] == "ambiguous_word"]
    assert len(amb) == 1 and amb[0]["severity"] == "warning" and amb[0]["values"] == ["EXPAT", "GCC"]
    r = resolve(c, "resident")
    assert values_of(r) == ["EXPAT", "GCC"] and r["ambiguous"] is True
    assert c.get("/api/dimensions").json()[0]["warnings"] >= 1


# ----------------------------------------------------------------------------- families
def test_families_must_point_at_listed_values(api):
    c, _ = api
    did = create_person_category(c)
    ok = c.patch(f"/api/dimensions/{did}", json={"families": [{"term": "gulf residents", "term_ar": "مقيمو الخليج",
                                                               "values": ["GCC", "EXPAT"]}]})
    assert ok.status_code == 200
    bad = c.patch(f"/api/dimensions/{did}", json={"families": [{"term": "x", "values": ["GCC"]}]})
    assert bad.status_code == 422 and "at least two" in bad.json()["detail"]
    bad = c.patch(f"/api/dimensions/{did}", json={"families": [{"term": "x", "values": ["GCC", "MARTIAN"]}]})
    assert bad.status_code == 422 and "MARTIAN" in bad.json()["detail"]
    bad = c.patch(f"/api/dimensions/{did}", json={"families": [{"term": "a", "values": ["GCC", "EXPAT"]}, {"term": "A", "values": ["GCC", "EXPAT"]}]})
    assert bad.status_code == 422 and "twice" in bad.json()["detail"]
    assert len(c.get(f"/api/dimensions/{did}").json()["families"]) == 1               # failed saves changed nothing

    r = resolve(c, "gulf residents")                                                  # one word, several values
    assert values_of(r) == ["EXPAT", "GCC"] and not r["ambiguous"] and r["matches"][0]["via"] == "family"
    assert values_of(resolve(c, "مقيمو الخليج")) == ["EXPAT", "GCC"]


def test_removing_a_value_warns_about_dependents_and_protects_applies_to_rules(api):
    c, _ = api
    did = create_person_category(c)
    vid = {v["value"]: v["id"] for v in c.get(f"/api/dimensions/{did}").json()["values_list"]}
    c.patch(f"/api/dimensions/{did}", json={"families": [{"term": "gulf residents", "values": ["GCC", "EXPAT"]}]})
    dep = c.get(f"/api/dimensions/{did}/values/{vid['GCC']}/dependents").json()
    assert dep["families"] == ["gulf residents"] and dep["aliases"] == 5 and dep["blocking"] is False
    assert c.delete(f"/api/dimensions/{did}/values/{vid['GCC']}").status_code == 409
    out = c.delete(f"/api/dimensions/{did}/values/{vid['GCC']}", params={"confirm": True}).json()
    assert out["removed"] == "GCC" and out["families_dropped"] == ["gulf residents"]   # left with one value => dropped
    assert c.get(f"/api/dimensions/{did}/validation").json()["issues"] == []

    tribe = c.post("/api/dimensions", json={"key": "tribe"}).json()["id"]
    c.patch(f"/api/dimensions/{tribe}", json={"applies_to": [{"dimension": "person_category", "values": ["CITIZEN"]}]})
    dep = c.get(f"/api/dimensions/{did}/values/{vid['CITIZEN']}/dependents").json()
    assert dep["blocking"] is True and dep["applies_to"] == [{"dimension": "tribe", "own": False}]
    r = c.delete(f"/api/dimensions/{did}/values/{vid['CITIZEN']}", params={"confirm": True})
    assert r.status_code == 409 and "applies to" in r.json()["detail"]                  # confirming cannot override it
    assert c.delete(f"/api/dimensions/{did}").status_code == 409                       # nor can deleting the dimension
    c.patch(f"/api/dimensions/{tribe}", json={"applies_to": []})
    assert c.delete(f"/api/dimensions/{did}/values/{vid['CITIZEN']}", params={"confirm": True}).status_code == 200


# ----------------------------------------------------------------------------- applies to
def test_applies_to_is_a_validated_structured_rule_exported_as_an_instruction(api):
    c, _ = api
    create_person_category(c)
    tribe = c.post("/api/dimensions", json={"key": "tribe", "label": "Tribe", "label_ar": "القبيلة"}).json()["id"]
    for body, word in [([{"dimension": "ghost", "values": ["X"]}], "unknown dimension"),
                       ([{"dimension": "person_category", "values": []}], "at least one value"),
                       ([{"dimension": "person_category", "values": ["MARTIAN"]}], "MARTIAN")]:
        r = c.patch(f"/api/dimensions/{tribe}", json={"applies_to": body})
        assert r.status_code == 422 and word in r.json()["detail"], r.text
    assert c.get(f"/api/dimensions/{tribe}").json()["applies_to"] == []

    c.patch(f"/api/dimensions/{tribe}", json={"applies_to": [{"dimension": "person_category", "values": ["CITIZEN"]}],
                                              "applies_note": "Tribes only exist for citizens.",
                                              "applies_note_ar": "القبائل للمواطنين فقط.", "status": "published"})
    doc = c.get("/agent/dimensions/tribe", params={"lang": "en"}).json()["applies_to"]
    assert doc["everyone"] is False and doc["conditions"] == [{"dimension": "person_category", "values": ["CITIZEN"]}]
    assert "restrict the data to person_category = CITIZEN" in doc["instruction"] and "Measure shares" in doc["instruction"]
    assert doc["instruction"].endswith("Tribes only exist for citizens.")
    ar = c.get("/agent/dimensions/tribe", params={"lang": "ar"}).json()["applies_to"]
    assert "القبيلة" in ar["instruction"] and "القبائل للمواطنين فقط" in ar["instruction"]
    both = c.get("/agent/dimensions/tribe", params={"lang": "both"}).json()["applies_to"]
    assert "instruction" in both and "instruction_ar" in both
    assert c.get("/agent/dimensions/person_category").json()["applies_to"] == {"everyone": True}

    # circular rules are allowed but flagged
    pc = c.get("/api/dimensions").json()
    pid = next(d["id"] for d in pc if d["key"] == "person_category")
    c.patch(f"/api/dimensions/{pid}", json={"applies_to": [{"dimension": "tribe", "values": []}]})  # tribe has no values
    assert c.get(f"/api/dimensions/{pid}").json()["applies_to"] == []


def test_applies_to_circular_rules_get_a_warning(api):
    c, _ = api
    a = c.post("/api/dimensions", json={"key": "alpha"}).json()["id"]
    b = c.post("/api/dimensions", json={"key": "beta"}).json()["id"]
    c.post(f"/api/dimensions/{a}/values", json={"value": "A1"})
    c.post(f"/api/dimensions/{b}/values", json={"value": "B1"})
    c.patch(f"/api/dimensions/{a}", json={"applies_to": [{"dimension": "beta", "values": ["B1"]}]})
    c.patch(f"/api/dimensions/{b}", json={"applies_to": [{"dimension": "alpha", "values": ["A1"]}]})
    codes = [i["code"] for i in c.get(f"/api/dimensions/{a}/validation").json()["issues"]]
    assert "applies_circular" in codes


# ----------------------------------------------------------------------------- bindings and what agents see
def test_binding_columns_visibility_and_the_agent_export(api):
    c, Local = api
    tables, cols = lake(Local, c)
    did = create_person_category(c, publish=False, bind=[cols[("population", "person_category")]])
    assert c.get("/agent/dimensions").json() == []                                    # drafts are invisible to agents
    assert c.get("/agent/dimensions/person_category").status_code == 404
    assert resolve(c, "residents")["matches"] == []

    r = c.post(f"/api/dimensions/{did}/bindings", json={"column_ids": [cols[("nationality", "person_category")]]})
    assert r.status_code == 200 and len(r.json()["bindings_list"]) == 2
    other = c.post("/api/dimensions", json={"key": "category2"}).json()["id"]
    r = c.post(f"/api/dimensions/{other}/bindings", json={"column_ids": [cols[("population", "person_category")]]})
    assert r.status_code == 409 and "already belongs to" in r.json()["detail"]
    found = c.get("/api/dimensions/columns", params={"q": "person_category"}).json()
    assert {f["table"]: f["bound_to"] for f in found} == {"wh.sales.population": "person_category", "wh.sales.nationality": "person_category"}

    c.patch(f"/api/dimensions/{did}", json={"status": "published"})
    assert [d["key"] for d in c.get("/agent/dimensions").json()] == ["person_category"]
    d = c.get("/agent/dimensions/person_category").json()
    assert d["columns"] == ["wh.sales.population.person_category", "wh.sales.nationality.person_category"]
    expat = next(v for v in d["values"] if v["value"] == "EXPAT")
    assert expat["label"] == "Expat" and expat["aliases"] == ["resident", "residents", "expat", "expats", "expatriates"]
    assert [v["value"] for v in d["values"]] == ["CITIZEN", "EXPAT", "GCC", "VISITOR"]

    # hidden or unpublished columns are not advertised
    c.patch(f"/api/columns/{cols[('nationality', 'person_category')]}", json={"quarantined": True})
    assert c.get("/agent/dimensions/person_category").json()["columns"] == ["wh.sales.population.person_category"]
    c.patch(f"/api/tables/{tables['population']}", json={"status": "draft"})
    assert c.get("/agent/dimensions/person_category").json()["columns"] == []
    assert c.delete(f"/api/dimensions/{did}/bindings/{cols[('population', 'person_category')]}").status_code == 200
    assert c.delete(f"/api/dimensions/{did}/bindings/{cols[('population', 'person_category')]}").status_code == 404


def test_languages_in_the_dimension_export(api):
    c, _ = api
    create_person_category(c)
    en = c.get("/agent/dimensions/person_category", params={"lang": "en"}).json()
    assert en["label"] == "Person category" and en["synonyms"] == ["category"]
    cit = next(v for v in en["values"] if v["value"] == "CITIZEN")
    assert cit["label"] == "Citizen" and cit["aliases"] == ["citizens", "citizen", "nationals", "emiratis"]   # Latin only
    ar = c.get("/agent/dimensions/person_category", params={"lang": "ar"}).json()
    assert ar["label"] == "فئة الشخص" and ar["synonyms"][:2] == ["فئة", "الفئة"]
    cit = next(v for v in ar["values"] if v["value"] == "CITIZEN")
    assert cit["label"] == "مواطن" and cit["aliases"][:3] == ["مواطن", "مواطنون", "مواطنين"]
    both = c.get("/agent/dimensions/person_category", params={"lang": "both"}).json()
    cit = next(v for v in both["values"] if v["value"] == "CITIZEN")
    assert cit["aliases_ar"] == ["مواطن", "مواطنون", "مواطنين"] and cit["label_ar"] == "مواطن"

    text = c.get("/agent/dimensions", params={"full": True, "format": "yaml", "lang": "both"}).text
    assert "key: person_category" in text and "aliases_ar" in text and "مقيمين" in text
    assert c.get("/agent/dimensions", params={"full": True, "format": "json"}).json()[0]["key"] == "person_category"
    summary = c.get("/agent/dimensions").json()[0]
    assert summary == {"key": "person_category", "label": "Person category", "description": summary["description"], "values": 4}


def test_a_tables_context_names_its_dimensions_and_caps_long_lists(api):
    c, Local = api
    tables, cols = lake(Local, c)
    did = create_person_category(c, bind=[cols[("population", "person_category")]])
    c.patch(f"/api/dimensions/{did}", json={"applies_to": [{"dimension": "person_category", "values": ["CITIZEN", "EXPAT"]}]})
    text = c.get("/agent/tables/wh.sales.population/context").text
    assert "dimension: person_category" in text                                       # on the column
    assert "dimensions:" in text and "value: CITIZEN" in text and "label: Citizen" in text
    assert "restrict the data to person_category = CITIZEN, EXPAT" in " ".join(text.split())     # (YAML wraps lines)
    assert "citizens" not in text                                                    # aliases stay out of the table context
    ar = c.get("/agent/tables/wh.sales.population/context", params={"lang": "ar"}).text
    assert "label: مواطن" in ar
    assert "dimensions:" not in c.get("/agent/tables/wh.sales.nationality/context").text   # not bound: nothing added

    c.post(f"/api/dimensions/{did}/values/bulk", json={"values": [{"value": f"V{i}"} for i in range(40)]})
    ctx = c.get("/agent/tables/wh.sales.population/context", params={"format": "json"}).text
    import json as _json
    block = _json.loads(ctx)[0]["dimensions"][0]
    assert len(block["values"]) == 30 and block["values_total"] == 44 and "resolve_value" in block["note"]
    c.patch(f"/api/dimensions/{did}", json={"status": "draft"})
    assert "dimensions:" not in c.get("/agent/tables/wh.sales.population/context").text    # unpublished: not exposed


def test_domain_restricted_keys_only_see_dimensions_in_their_domains(api):
    c, Local = api
    tables, cols = lake(Local, c)
    create_person_category(c, bind=[cols[("population", "person_category")]])           # a sales table
    make_user(c, "admin", "boss@example.com")
    hr = c.post("/api/admin/keys", json={"name": "hr bot", "allowed_domains": ["hr"]}).json()["secret"]
    sales = c.post("/api/admin/keys", json={"name": "sales bot", "allowed_domains": ["sales"]}).json()["secret"]
    from fastapi.testclient import TestClient
    from app.main import app
    bot = TestClient(app)
    h = lambda k: {"X-API-Key": k}  # noqa: E731
    assert bot.get("/agent/dimensions", headers=h(hr)).json() == []
    assert bot.get("/agent/dimensions/person_category", headers=h(hr)).status_code == 404
    assert bot.get("/agent/resolve-value", params={"text": "residents"}, headers=h(hr)).json()["matches"] == []
    assert [d["key"] for d in bot.get("/agent/dimensions", headers=h(sales)).json()] == ["person_category"]
    assert bot.get("/agent/resolve-value", params={"text": "residents"}, headers=h(sales)).json()["matches"][0]["value"] == "EXPAT"


# ----------------------------------------------------------------------------- load values from the data
class FakeLake:
    """Stands in for Trino: distinct values per (table, column)."""
    data = {("population", "person_category"): [("CITIZEN", 500), ("EXPAT", 300), ("SPACE_ALIEN", 2)],
            ("nationality", "person_category"): [("CITIZEN", 50), ("DIASPORA", 7)]}
    boom = False
    limit_seen = None

    def __init__(self, config):
        pass

    def distinct_values(self, schema, table, column, limit=200, sample_rows=0):
        FakeLake.limit_seen = limit
        if FakeLake.boom:
            raise ConnectionError("lake is down")
        return {"values": self.data[(table, column)], "truncated": False}


def test_loading_values_from_the_data(api, monkeypatch):
    c, Local = api
    tables, cols = lake(Local, c)
    pop, nat = cols[("population", "person_category")], cols[("nationality", "person_category")]
    did = create_person_category(c, bind=[pop, nat])
    import app.dimensions_api as api_mod
    monkeypatch.setattr(api_mod, "get_connector", lambda kind, config: FakeLake(config))
    FakeLake.boom = False

    r = c.post(f"/api/dimensions/{did}/load-values", json={}).json()
    by = {v["value"]: v for v in r["values"]}
    assert by["CITIZEN"]["count"] == 550 and sorted(by["CITIZEN"]["columns"]) == ["wh.sales.nationality.person_category", "wh.sales.population.person_category"]
    assert by["CITIZEN"]["in_vocabulary"] is True and by["SPACE_ALIEN"]["in_vocabulary"] is False
    assert [v["value"] for v in r["values"]][:2] == ["CITIZEN", "EXPAT"]                    # most frequent first
    assert r["missing_from_data"] == ["GCC", "VISITOR"] and r["errors"] == [] and FakeLake.limit_seen == 200
    assert c.post(f"/api/dimensions/{did}/load-values", json={"column_id": nat}).json()["values"][0]["value"] == "CITIZEN"

    new = [v["value"] for v in r["values"] if not v["in_vocabulary"]]                      # the caller picks what to add
    out = c.post(f"/api/dimensions/{did}/values/bulk", json={"values": [{"value": v} for v in new]}).json()
    assert out["added"] == 2
    assert c.post(f"/api/dimensions/{did}/load-values", json={}).json()["values"][0]["in_vocabulary"] is True

    # personal data and hidden columns are never read
    c.patch(f"/api/columns/{nat}", json={"pii": True})
    r = c.post(f"/api/dimensions/{did}/load-values", json={}).json()
    assert [s["column"] for s in r["skipped"]] == ["wh.sales.nationality.person_category"] and "personal data" in r["skipped"][0]["reason"]
    assert {v["value"] for v in r["values"]} == {"CITIZEN", "EXPAT", "SPACE_ALIEN"}
    with Local() as sess:                         # un-marking PII is a staged edit; apply it as a published revision would
        from app.models import Column
        sess.get(Column, nat).pii = False
        sess.commit()
    c.patch(f"/api/columns/{nat}", json={"quarantined": True})
    r = c.post(f"/api/dimensions/{did}/load-values", json={}).json()
    assert "hidden for review" in r["skipped"][0]["reason"]

    FakeLake.boom = True                                                                  # a down lake is reported, not a 500
    r = c.post(f"/api/dimensions/{did}/load-values", json={})
    assert r.status_code == 200 and "lake is down" in r.json()["errors"][0]["error"] and r.json()["values"] == []
    empty = c.post("/api/dimensions", json={"key": "unbound"}).json()["id"]
    assert c.post(f"/api/dimensions/{empty}/load-values", json={}).status_code == 400


# ----------------------------------------------------------------------------- governance
def test_permissions_events_audit_and_publishing_guard(api):
    c, Local = api
    did = create_person_category(c, publish=False)
    steward = make_user(c, "steward", "s@example.com")
    viewer = make_user(c, "viewer", "v@example.com")
    assert viewer.get("/api/dimensions").status_code == 200 and viewer.get(f"/api/dimensions/{did}").status_code == 200
    for call in (lambda: viewer.post("/api/dimensions", json={"key": "x1"}),
                 lambda: viewer.patch(f"/api/dimensions/{did}", json={"label": "x"}),
                 lambda: viewer.post(f"/api/dimensions/{did}/values", json={"value": "Z"}),
                 lambda: viewer.delete(f"/api/dimensions/{did}")):
        assert call().status_code == 403
    assert steward.post(f"/api/dimensions/{did}/values", json={"value": "NEW"}).status_code == 200
    assert not [e for e in c.events if e[0] == "dimension.updated"]                       # a draft is nobody's business

    steward.patch(f"/api/dimensions/{did}", json={"status": "published"})
    steward.post(f"/api/dimensions/{did}/values", json={"value": "OTHER", "aliases": ["misc"]})
    events = [e for e in c.events if e[0] == "dimension.updated"]
    assert events[-1][1] == {"key": "person_category", "change": "added value OTHER"}

    log = c.get("/api/admin/audit", params={"actor": "s@example.com"}).json()["items"]
    assert any(a["target"] == "dimension person_category" and a["field"] == "value OTHER" for a in log)
    assert any(a["field"] == "status" and a["new"] == "published" for a in log)

    with Local() as s:                                                                    # an invalid state cannot be published
        d = s.query(Dimension).one()
        d.status, d.families = "draft", [{"term": "bad", "values": ["GCC", "NOPE"]}]
        s.commit()
    r = steward.patch(f"/api/dimensions/{did}", json={"status": "published"})
    assert r.status_code == 422 and "Cannot publish" in r.json()["detail"] and "NOPE" in r.json()["detail"]
    assert c.get("/api/dimensions").json()[0]["errors"] == 1


def test_deleting_a_source_removes_its_dimension_bindings(api):
    c, Local = api
    tables, cols = lake(Local, c)
    did = create_person_category(c, bind=[cols[("population", "person_category")]])
    sid = c.get("/api/sources").json()[0]["id"]
    assert c.delete(f"/api/sources/{sid}").status_code == 200
    with Local() as s:
        assert s.query(DimensionBinding).count() == 0
    d = c.get(f"/api/dimensions/{did}").json()
    assert d["bindings_list"] == [] and d["values"] == 4                                  # the vocabulary itself survives


def test_the_table_editor_shows_which_dimension_a_column_belongs_to(api):
    c, Local = api
    tables, cols = lake(Local, c)
    create_person_category(c, publish=False, bind=[cols[("population", "person_category")]])
    editor = {x["name"]: x for x in c.get(f"/api/tables/{tables['population']}").json()["columns"]}
    assert editor["person_category"]["dimension"] == {"id": editor["person_category"]["dimension"]["id"], "key": "person_category",
                                                      "label": "Person category", "status": "draft"}
    assert editor["headcount"]["dimension"] is None


def test_mcp_tools_resolve_and_describe(api, monkeypatch):
    c, Local = api
    create_person_category(c)
    monkeypatch.setattr(mcp_server, "SessionLocal", Local)
    assert [d["key"] for d in mcp_server.list_dimensions()] == ["person_category"]
    r = mcp_server.resolve_value("residents")
    assert r["matches"][0]["value"] == "EXPAT" and r["ambiguous"] is False
    assert mcp_server.resolve_value("مقيمين", lang="ar")["matches"][0]["label"] == "مقيم"
    d = mcp_server.describe_dimension("person_category")
    assert [v["value"] for v in d["values"]] == ["CITIZEN", "EXPAT", "GCC", "VISITOR"]
    with pytest.raises(ValueError):
        mcp_server.describe_dimension("nope")
