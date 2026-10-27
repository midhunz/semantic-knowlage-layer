import pytest
from conftest import fresh_engine, go_live  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

import app.db as db  # noqa: E402

db.engine.dispose()
db.engine = fresh_engine()
db.SessionLocal.configure(bind=db.engine)

from app.connectors.base import ColumnMeta, TableMeta  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Source  # noqa: E402
from app.services.sync import apply_sync  # noqa: E402

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def _clean_schema():
    """These tests share state on purpose (one story, top to bottom) but must start from nothing,
    even when another module left rows behind in a shared database such as Postgres."""
    db.Base.metadata.drop_all(db.engine)
    db.Base.metadata.create_all(db.engine)


def _meta(extra_col=False, retype=False):
    cols = [ColumnMeta("order_id", "bigint", False, 1),
            ColumnMeta("net_amount", "varchar" if retype else "double", True, 2)]
    if extra_col:
        cols.append(ColumnMeta("channel", "varchar", True, 3))
    return [TableMeta("sales", "fact_orders", cols, "iceberg")]


def test_sync_preserves_semantics_and_flags_drift():
    with db.SessionLocal() as s:
        src = Source(name="lake", config={})
        s.add(src)
        s.commit()
        assert apply_sync(s, src, _meta())["tables_added"] == 1
        table = src.tables[0]
        table.description = "Orders"
        table.columns[1].description = "Net revenue"
        s.commit()

        stats = apply_sync(s, src, _meta(extra_col=True, retype=True))
        assert stats["columns_added"] == 1 and stats["columns_changed"] == 1
        assert table.description == "Orders"
        assert table.columns[1].description == "Net revenue" and table.columns[1].needs_review

        stats = apply_sync(s, src, _meta())
        assert stats["columns_removed"] == 1
        assert [c for c in table.columns if c.name == "channel"][0].removed


def test_publish_flow_and_agent_context_hides_unpublished_and_pii():
    tid = client.get("/api/tables").json()[0]["id"]
    assert client.get("/agent/tables/sales.fact_orders/context").status_code == 404

    t = client.get(f"/api/tables/{tid}").json()
    amount = next(c for c in t["columns"] if c["name"] == "net_amount")
    order = next(c for c in t["columns"] if c["name"] == "order_id")
    client.patch(f"/api/columns/{amount['id']}", json={"role": "measure", "default_aggregation": "sum",
                                                       "synonyms": ["revenue"], "example_values": [1, 2]})
    client.patch(f"/api/columns/{order['id']}", json={"pii": True, "example_values": ["secret"]})
    client.patch(f"/api/tables/{tid}", json={"grain": "one row per order", "table_type": "fact",
                                             "status": "published"})
    term = client.post("/api/glossary", json={"term": "Revenue", "definition": "Net sales", "synonyms": ["sales"]}).json()
    assert client.get("/agent/glossary/resolve", params={"term": "sales"}).json() == []      # a draft is not visible
    go_live(client, "glossary", term["id"])

    ctx = client.get("/agent/tables/sales.fact_orders/context").text
    assert "one row per order" in ctx and "revenue" in ctx
    assert "secret" not in ctx
    assert client.get("/agent/glossary/resolve", params={"term": "sales"}).json()[0]["term"] == "Revenue"
    assert client.get("/agent/search", params={"q": "revenue"}).json()[0]["table"] == "lake.sales.fact_orders"
    assert len(client.get("/api/audit").json()) > 0


# ---------------------------------------------------------------- scale + bilingual
def _seed_many():
    """Two sources, several schemas, a shared `customer_id` column name."""
    with db.SessionLocal() as s:
        for name in ("wh", "crm"):
            src = Source(name=name, config={})
            s.add(src)
            s.commit()
            apply_sync(s, src, [
                TableMeta(sch, tbl, [ColumnMeta("customer_id", "bigint", False, 1),
                                     ColumnMeta("order_date", "date", True, 2),
                                     ColumnMeta("net_amount", "double", True, 3)])
                for sch in ("a", "b") for tbl in ("t1", "t2")
            ])


def test_scoped_sync_does_not_remove_other_schemas():
    _seed_many()
    with db.SessionLocal() as s:
        src = s.query(Source).filter_by(name="wh").one()
        stats = apply_sync(s, src, [TableMeta("a", "t1", [ColumnMeta("customer_id", "bigint")])], scope=["a"])
        assert stats["tables_removed"] == 1  # a.t2 only; schema b untouched
        assert not [t for t in src.tables if t.schema_name == "b" and t.removed]


def test_grid_filters_pagination_bulk_and_tree():
    page = client.get("/api/catalog/tables", params={"source_id": 1, "page_size": 2}).json()
    assert len(page["items"]) <= 2 and page["total"] >= 1

    wh = client.get("/api/catalog/tables", params={"schema": "a", "page_size": 200}).json()
    assert wh["total"] >= 2 and all(r["schema"] == "a" for r in wh["items"])

    # bulk by filter: set domain+type for every undocumented table in schema "b"
    r = client.post("/api/catalog/tables/bulk-update", json={
        "filters": {"schema": "b", "missing": "description"},
        "patch": {"domain": "finance", "table_type": "fact"}}).json()
    assert r["matched"] >= 2 and r["changed"] == r["matched"]
    assert client.get("/api/catalog/tables", params={"domain": "finance"}).json()["total"] == r["matched"]

    tree = client.get("/api/catalog/tree").json()
    assert {s["name"] for s in tree} >= {"wh", "crm"}
    assert client.get("/api/catalog/stats").json()["totals"]["tables"] >= 8


def test_column_dictionary_applies_to_all_same_named_columns_bilingual():
    groups = client.get("/api/catalog/column-groups", params={"q": "customer_id"}).json()["items"]
    g = groups[0]
    assert g["name"] == "customer_id" and g["occurrences"] >= 7

    r = client.post("/api/catalog/column-groups/apply", json={
        "name": "customer_id", "only_empty": True,
        "patch": {"description": "Unique customer key", "description_ar": "المعرّف الفريد للعميل",
                  "synonyms_ar": ["رقم العميل"]}}).json()
    assert r["updated"] == r["matched"] >= 7
    # second run with only_empty=True changes nothing
    assert client.post("/api/catalog/column-groups/apply", json={
        "name": "customer_id", "patch": {"description": "X"}}).json()["updated"] == 0

    done = client.get("/api/catalog/column-groups", params={"q": "customer_id"}).json()["items"][0]
    assert done["documented"] == done["documented_ar"] == done["occurrences"]


def test_arabic_agent_output_and_diacritic_insensitive_search():
    tid = client.get("/api/catalog/tables", params={"schema": "b", "source_id": 2}).json()["items"][0]["id"]
    client.patch(f"/api/tables/{tid}", json={"status": "published", "description": "Orders",
                                             "description_ar": "الطلبات", "grain_ar": "صف لكل طلب"})
    full = client.get(f"/api/tables/{tid}").json()["full_name"]
    ar = client.get(f"/agent/tables/{full}/context", params={"lang": "ar"}).text
    assert "الطلبات" in ar and "المعرّف الفريد للعميل" in ar
    both = client.get(f"/agent/tables/{full}/context", params={"lang": "both"}).text
    assert "description_ar" in both and "description:" in both
    # diacritics/alef variants are ignored: search with an unvoweled form of a voweled synonym
    hits = client.get("/agent/search", params={"q": "رقم العميل", "lang": "ar"}).json()
    assert any(h.get("table") == full for h in hits)
    assert client.get("/agent/search", params={"q": "الطلبات"}).json()
    # a 2-part name resolves while unique, and is rejected once another source publishes the same one
    assert client.get("/agent/tables/b.t1/context").status_code == 200
    other = next(r for r in client.get("/api/catalog/tables", params={"schema": "b", "source": "crm"}).json()["items"]
                 if r["name"] == "t1" and r["source"] == "crm")
    client.patch(f"/api/tables/{other['id']}", json={"status": "published"})
    assert client.get("/agent/tables/b.t1/context").status_code == 409
    assert client.get("/agent/tables/crm.b.t1/context").status_code == 200


def test_csv_roundtrip_arabic():
    csv_text = client.get("/api/catalog/export/columns.csv", params={"schema": "b", "source_id": 2}).content
    assert csv_text.startswith(b"\xef\xbb\xbf")  # BOM for Excel
    body = ("source,schema,table,column,description_ar\ncrm,b,t1,net_amount,صافي المبلغ\n"
            "crm,b,t1,missing_col,x\n").encode("utf-8")
    r = client.post("/api/catalog/import/columns", content=body).json()
    assert r["updated"] == 1 and len(r["errors"]) == 1


# ---------------------------------------------------------------- source CRUD
def test_source_crud_validation_and_cascade_delete():
    cfg = {"host": "x", "port": 1, "catalog": "c", "user": "u"}
    assert client.post("/api/sources", json={"name": "bad.name", "config": cfg}).status_code == 422
    assert client.post("/api/sources", json={"name": "has space", "config": cfg}).status_code == 422
    made = client.post("/api/sources", json={"name": "scratch", "config": cfg})
    assert made.status_code == 200
    sid = made.json()["id"]
    assert client.post("/api/sources", json={"name": "scratch", "config": cfg}).status_code == 409

    # rename + reconfigure; renaming onto an existing name is rejected
    assert client.put(f"/api/sources/{sid}", json={"name": "scratch2", "config": {**cfg, "port": 2}}).json()["name"] == "scratch2"
    assert client.put(f"/api/sources/{sid}", json={"name": "wh", "config": cfg}).status_code == 409
    assert client.put(f"/api/sources/{sid}", json={"name": "scratch2", "config": cfg}).status_code == 200

    with db.SessionLocal() as s:
        src = s.get(Source, sid)
        apply_sync(s, src, [TableMeta("z", "t", [ColumnMeta("id", "bigint"), ColumnMeta("ref", "bigint")])])
        t = src.tables[0]
        t.description = "keep me?"
        from app.models import Metric, Relationship
        m = Metric(name="m_scratch", sql_expression="COUNT(*)", base_table_id=t.id)
        s.add(m)
        s.add(Relationship(from_column_id=t.columns[0].id, to_column_id=t.columns[1].id))
        s.commit()
        table_id = t.id

    impact = client.get(f"/api/sources/{sid}/impact").json()
    assert impact["tables"] == 1 and impact["columns"] == 2 and impact["curated_tables"] == 1 and impact["metrics"] == 1
    assert client.get("/api/sources").json()[0].keys() >= {"tables", "published", "last_synced_at"}

    res = client.delete(f"/api/sources/{sid}")
    assert res.json() == {"deleted": "scratch2", "tables_removed": 1}
    assert client.get(f"/api/tables/{table_id}").status_code == 404
    assert client.delete(f"/api/sources/{sid}").status_code == 404
    with db.SessionLocal() as s:  # metric survives, detached from the removed table
        assert s.query(Metric).filter_by(name="m_scratch").one().base_table_id is None
        assert s.query(Relationship).count() == 0


def test_connection_failures_are_clean_errors_not_500s():
    r = client.post("/api/sources/test", json={"name": "nope", "config": {"host": "127.0.0.1", "port": 1,
                                                                           "catalog": "c", "user": "u"}})
    assert r.status_code == 502 and "detail" in r.json()
    assert client.post("/api/sources/test", json={"name": "nope", "config": {}}).status_code == 400


def test_natural_sort_and_worklist_counts_match_filters():
    names = [r["name"] for r in client.get("/api/catalog/tables", params={"schema": "a", "source_id": 2,
                                                                         "page_size": 200}).json()["items"]]
    assert names == sorted(names, key=lambda n: (len(n), n))  # t1 < t2 style ordering preserved
    from app.catalog import _nat
    assert sorted(["table_10", "table_2", "table_1"], key=_nat) == ["table_1", "table_2", "table_10"]

    wl = client.get("/api/catalog/stats").json()["worklists"]
    for key, params in (("description", {"missing": "description"}), ("arabic", {"missing": "arabic"}),
                        ("grain", {"missing": "grain"}), ("columns", {"missing": "columns"}),
                        ("needs_review", {"needs_review": True}), ("draft", {"status": "draft"})):
        total = client.get("/api/catalog/tables", params={**params, "page_size": 1}).json()["total"]
        assert wl[key] == total, key  # the number on the pill equals what the pill filter returns
