"""Catalog-at-scale API: server-side grid, tree, facets, coverage, bulk edit, column dictionary,
and CSV round-trip. Designed for several sources and hundreds of tables."""

import csv
import io
import re
from collections import defaultdict

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app import i18n, schemas
from app.db import get_session
from app.models import AuditLog, Column, SchemaMeta, Source, Table, TableRevision
from app.auth import actor_of
from app.services import revisions, webhooks
from app.services.settings_store import get_settings

router = APIRouter(prefix="/api/catalog", tags=["catalog-scale"])
Db = Depends(get_session)

FILTER_KEYS = ("source_id", "schema", "status", "type", "domain", "owner", "needs_review", "missing",
               "q", "include_removed", "pending", "quarantined")
MISSING = ("description", "grain", "type", "owner", "domain", "arabic", "columns")


def filters_from_query(
    source_id: int | None = None, schema: str | None = None, status: str | None = None,
    type: str | None = None, domain: str | None = None, owner: str | None = None,
    needs_review: bool | None = None, missing: str | None = None, q: str | None = None,
    include_removed: bool = False, pending: bool = False, quarantined: bool = False,
) -> dict:
    return {k: v for k, v in dict(source_id=source_id, schema=schema, status=status, type=type,
                                  domain=domain, owner=owner, needs_review=needs_review,
                                  missing=missing, q=q, include_removed=include_removed,
                                  pending=pending, quarantined=quarantined).items()
            if v not in (None, "", False)}


Filters = Depends(filters_from_query)


def _blank(value) -> bool:
    return value is None or value == "" or value == [] or value == {} or value is False


# --------------------------------------------------------------------------- rows
def table_rows(session: Session, f: dict) -> list[dict]:
    """All tables matching filters, with column-coverage stats. ~700 rows is cheap to do in Python."""
    cs = (
        select(
            Column.table_id.label("tid"),
            func.count().label("n"),
            func.sum(case((func.coalesce(Column.description, "") != "", 1), else_=0)).label("doc_en"),
            func.sum(case((func.coalesce(Column.description_ar, "") != "", 1), else_=0)).label("doc_ar"),
            func.sum(case((Column.quarantined.is_(True), 1), else_=0)).label("quar"),
        ).where(Column.removed.is_(False)).group_by(Column.table_id)
    ).subquery()
    stmt = (
        select(Table, Source.name, cs.c.n, cs.c.doc_en, cs.c.doc_ar, cs.c.quar)
        .join(Source, Source.id == Table.source_id)
        .outerjoin(cs, cs.c.tid == Table.id)
    )
    if not f.get("include_removed"):
        stmt = stmt.where(Table.removed.is_(False))
    if "source_id" in f:
        stmt = stmt.where(Table.source_id == f["source_id"])
    for key, col in (("schema", Table.schema_name), ("status", Table.status), ("type", Table.table_type),
                     ("domain", Table.domain), ("owner", Table.owner)):
        if key in f:
            stmt = stmt.where(col == f[key])
    if "needs_review" in f:
        stmt = stmt.where(Table.needs_review.is_(bool(f["needs_review"])))
    pending_ids = set(session.scalars(select(TableRevision.table_id).where(TableRevision.status == "pending")))
    if f.get("pending"):
        stmt = stmt.where(Table.id.in_(pending_ids or [-1]))
    if f.get("quarantined"):
        stmt = stmt.where(func.coalesce(cs.c.quar, 0) > 0)
    m = f.get("missing")
    if m == "description":
        stmt = stmt.where(func.coalesce(Table.description, "") == "")
    elif m == "grain":
        stmt = stmt.where(func.coalesce(Table.grain, "") == "")
    elif m == "type":
        stmt = stmt.where(Table.table_type.is_(None))
    elif m == "owner":
        stmt = stmt.where(func.coalesce(Table.owner, "") == "")
    elif m == "domain":
        stmt = stmt.where(func.coalesce(Table.domain, "") == "")
    elif m == "arabic":
        stmt = stmt.where(func.coalesce(Table.description_ar, "") == "")
    elif m == "columns":
        stmt = stmt.where(func.coalesce(cs.c.doc_en, 0) < func.coalesce(cs.c.n, 0))

    blobs: dict[int, list] = defaultdict(list)
    if f.get("q"):
        for r in session.execute(select(Column.table_id, Column.name, Column.display_name,
                                        Column.display_name_ar, Column.description, Column.description_ar,
                                        Column.synonyms, Column.synonyms_ar).where(Column.removed.is_(False))):
            blobs[r[0]].extend([r[1], r[2], r[3], r[4], r[5], *(r[6] or []), *(r[7] or [])])

    rows = []
    for t, source_name, n, doc_en, doc_ar, quar in session.execute(stmt):
        if f.get("q") and not i18n.hit(f["q"], t.name, t.schema_name, source_name, t.display_name,
                                       t.display_name_ar, t.description, t.description_ar, t.domain,
                                       t.owner, blobs.get(t.id, [])):
            continue
        n, doc_en, doc_ar, quar = n or 0, doc_en or 0, doc_ar or 0, quar or 0
        en_parts = [bool(t.description), bool(t.grain), bool(t.table_type)]
        ar_parts = [bool(t.description_ar), bool(t.grain_ar)]
        rows.append({
            "id": t.id, "source_id": t.source_id, "source": source_name, "schema": t.schema_name,
            "name": t.name, "full_name": f"{source_name}.{t.schema_name}.{t.name}",
            "display_name": t.display_name, "display_name_ar": t.display_name_ar,
            "type": t.table_type, "domain": t.domain, "owner": t.owner, "status": t.status,
            "needs_review": t.needs_review, "removed": t.removed, "certified": t.certified,
            "has_description": bool(t.description), "has_grain": bool(t.grain),
            "has_description_ar": bool(t.description_ar),
            "columns": n, "columns_documented": doc_en, "columns_documented_ar": doc_ar,
            "row_count": t.row_count, "version": t.version,
            "quarantined": quar, "pending": t.id in pending_ids,
            "en": round((doc_en + sum(en_parts)) / (n + 3), 3),
            "ar": round((doc_ar + sum(ar_parts)) / (n + 2), 3),
        })
    return rows


# --------------------------------------------------------------------------- grid / tree
def _nat(text: str) -> list:
    """Natural sort key: table_2 before table_10."""
    return [int(p) if p.isdigit() else p.lower() for p in re.split(r"(\d+)", text or "")]


SORTS = {"name": lambda r: (_nat(r["source"]), _nat(r["schema"]), _nat(r["name"])), "status": lambda r: r["status"],
         "type": lambda r: r["type"] or "~", "domain": lambda r: r["domain"] or "~",
         "owner": lambda r: r["owner"] or "~", "en": lambda r: r["en"], "ar": lambda r: r["ar"],
         "columns": lambda r: r["columns"]}


@router.get("/tables")
def list_tables(f: dict = Filters, sort: str = "name", order: str = "asc", page: int = Query(1, ge=1),
                page_size: int = Query(50, ge=1, le=200), session: Session = Db):
    rows = table_rows(session, f)
    rows.sort(key=SORTS.get(sort, SORTS["name"]), reverse=order == "desc")
    start = (page - 1) * page_size
    return {"items": rows[start:start + page_size], "total": len(rows), "page": page, "page_size": page_size}


@router.get("/tree")
def tree(session: Session = Db):
    """Source → schema roll-up for the navigation tree (counts only; tables load via the grid)."""
    rows = table_rows(session, {})
    meta = {(s.source_id, s.name): s for s in session.scalars(select(SchemaMeta))}
    created = False
    for r in rows:  # schemas synced before schema records existed get one lazily
        if (r["source_id"], r["schema"]) not in meta:
            meta[(r["source_id"], r["schema"])] = sm = SchemaMeta(source_id=r["source_id"], name=r["schema"])
            session.add(sm)
            created = True
    if created:
        session.commit()
    by_source: dict[tuple[int, str], dict] = {}
    for src in session.scalars(select(Source).order_by(Source.name)):
        by_source[(src.id, src.name)] = {"id": src.id, "name": src.name, "kind": src.kind, "schemas": {}}
    for r in rows:
        node = by_source[(r["source_id"], r["source"])]["schemas"].setdefault(
            r["schema"], {"name": r["schema"], "tables": 0, "published": 0, "review": 0, "en": 0.0, "ar": 0.0})
        node["tables"] += 1
        node["published"] += r["status"] == "published"
        node["review"] += bool(r["needs_review"])
        node["en"] += r["en"]
        node["ar"] += r["ar"]
    out = []
    for (sid, _), src in by_source.items():
        schemas_ = []
        for node in sorted(src["schemas"].values(), key=lambda x: x["name"]):
            n = node["tables"]
            sm = meta.get((sid, node["name"]))
            schemas_.append({**node, "en": round(node["en"] / n, 3), "ar": round(node["ar"] / n, 3),
                             "schema_id": sm.id if sm else None})
        out.append({"id": src["id"], "name": src["name"], "kind": src["kind"], "schemas": schemas_,
                    "tables": sum(s["tables"] for s in schemas_)})
    return out


@router.get("/facets")
def facets(session: Session = Db):
    rows = table_rows(session, {})
    count = lambda key: sorted(  # noqa: E731
        ({"value": v, "count": c} for v, c in _count(r[key] for r in rows) if v), key=lambda x: -x["count"])
    return {"domains": count("domain"), "owners": count("owner"), "types": count("type"),
            "statuses": count("status")}


def _count(values):
    d: dict = defaultdict(int)
    for v in values:
        d[v] += 1
    return d.items()


@router.get("/stats")
def stats(f: dict = Filters, session: Session = Db):
    rows = table_rows(session, f)

    def roll(key):
        groups: dict = defaultdict(lambda: {"tables": 0, "published": 0, "review": 0, "en": 0.0, "ar": 0.0})
        for r in rows:
            g = groups[r[key] or "(none)"]
            g["tables"] += 1
            g["published"] += r["status"] == "published"
            g["review"] += bool(r["needs_review"])
            g["en"] += r["en"]
            g["ar"] += r["ar"]
        return sorted(({"name": k, **v, "en": round(v["en"] / v["tables"], 3),
                        "ar": round(v["ar"] / v["tables"], 3)} for k, v in groups.items()),
                      key=lambda x: x["en"])

    n = len(rows) or 1
    return {
        "totals": {
            "tables": len(rows), "published": sum(r["status"] == "published" for r in rows),
            "review": sum(bool(r["needs_review"]) for r in rows),
            "columns": sum(r["columns"] for r in rows),
            "en": round(sum(r["en"] for r in rows) / n, 3), "ar": round(sum(r["ar"] for r in rows) / n, 3),
            "pending": sum(bool(r["pending"]) for r in rows),
            "quarantined_columns": sum(r["quarantined"] for r in rows),
            "no_description": sum(not r["has_description"] for r in rows),
            "no_arabic": sum(not r["has_description_ar"] for r in rows),
            "unpublished": sum(r["status"] != "published" for r in rows),
        },
        "worklists": {  # counts behind the catalog quick-filters; keys match the `missing`/status filters
            "all": len(rows),
            "needs_review": sum(bool(r["needs_review"]) for r in rows),
            "description": sum(not r["has_description"] for r in rows),
            "grain": sum(not r["has_grain"] for r in rows),
            "arabic": sum(not r["has_description_ar"] for r in rows),
            "columns": sum(r["columns_documented"] < r["columns"] for r in rows),
            "draft": sum(r["status"] != "published" for r in rows),
            "published": sum(r["status"] == "published" for r in rows),
            "pending": sum(bool(r["pending"]) for r in rows),
            "quarantined": sum(1 for r in rows if r["quarantined"]),
        },
        "by_source": roll("source"), "by_domain": roll("domain"), "by_type": roll("type"),
    }


# --------------------------------------------------------------------------- bulk table edit
def _audit(session: Session, entity: str, obj, field: str, old, new, actor: str, staged: bool = False) -> None:
    revisions.audit(session, entity, obj, field, old, new, actor, staged)


@router.post("/tables/bulk-update")
def bulk_update(body: schemas.BulkTableUpdate, request: Request, session: Session = Db):
    """Content edits on published tables are staged for review; status and review flags apply at once."""
    if body.ids is None and body.filters is None:
        raise HTTPException(400, "Provide ids or filters")
    # explicit `ids` always wins (an empty list means "nothing"); `filters: {}` means every table
    ids = body.ids if body.ids is not None else [r["id"] for r in table_rows(session, body.filters or {})]
    patch = body.patch.model_dump(exclude_unset=True)
    if not patch:
        raise HTTPException(400, "Empty patch")
    actor = actor_of(request)
    cfg = get_settings(session)
    changed, staged, blocked = 0, 0, []
    for t in session.scalars(select(Table).where(Table.id.in_(ids))):
        data = dict(patch)
        status = data.pop("status", None)
        res = revisions.edit_table(session, t, data, actor)
        moved = False
        if status is not None and status != t.status:
            problems = revisions.transition_status(session, t, status, actor, cfg=cfg, raise_on_block=False)
            if problems:   # skip the status change for this table, keep going with the rest
                blocked.append({"table": t.full_name, "reason": "; ".join(problems)})
            else:
                moved = True
        changed += bool(res.live or moved)
        staged += bool(res.staged)
    session.commit()
    return {"matched": len(ids), "changed": changed, "staged": staged, "blocked": len(blocked),
            "blocked_examples": blocked[:5]}


# --------------------------------------------------------------------------- column dictionary
SHARED_FIELDS = ("description", "description_ar", "display_name", "display_name_ar", "role",
                 "semantic_type", "unit", "default_aggregation", "synonyms", "synonyms_ar",
                 "allowed_values", "allowed_values_ar")


@router.get("/column-groups")
def column_groups(q: str | None = None, missing: str | None = None, source_id: int | None = None,
                  schema: str | None = None, sort: str = "occurrences", page: int = Query(1, ge=1),
                  page_size: int = Query(50, ge=1, le=200), session: Session = Db):
    """Columns grouped by name across all tables: document `customer_id` once, apply to every table."""
    stmt = (
        select(
            Column.name,
            func.count().label("occurrences"),
            func.count(func.distinct(Column.table_id)).label("tables"),
            func.sum(case((func.coalesce(Column.description, "") != "", 1), else_=0)).label("doc_en"),
            func.sum(case((func.coalesce(Column.description_ar, "") != "", 1), else_=0)).label("doc_ar"),
            func.min(Column.data_type).label("data_type"),
            func.count(func.distinct(Column.data_type)).label("type_count"),
        )
        .join(Table, Table.id == Column.table_id)
        .where(Column.removed.is_(False), Table.removed.is_(False))
        .group_by(Column.name)
    )
    if source_id:
        stmt = stmt.where(Table.source_id == source_id)
    if schema:
        stmt = stmt.where(Table.schema_name == schema)
    groups = []
    for r in session.execute(stmt):
        groups.append({"name": r.name, "occurrences": r.occurrences, "tables": r.tables,
                       "documented": r.doc_en or 0, "documented_ar": r.doc_ar or 0,
                       "data_type": r.data_type, "mixed_types": r.type_count > 1})
    if q:
        groups = [g for g in groups if i18n.norm(q) in i18n.norm(g["name"])]
    if missing == "description":
        groups = [g for g in groups if g["documented"] < g["occurrences"]]
    elif missing == "arabic":
        groups = [g for g in groups if g["documented_ar"] < g["occurrences"]]
    keys = {"occurrences": lambda g: -g["occurrences"], "name": lambda g: g["name"],
            "undocumented": lambda g: -(g["occurrences"] - g["documented"])}
    groups.sort(key=keys.get(sort, keys["occurrences"]))
    start = (page - 1) * page_size
    items = groups[start:start + page_size]
    # prefill each visible group with a representative already-documented column
    names = [g["name"] for g in items]
    reps: dict[str, Column] = {}
    if names:
        for c in session.scalars(select(Column).where(Column.name.in_(names), Column.removed.is_(False))
                                 .order_by(Column.id)):
            cur = reps.get(c.name)
            score = sum(not _blank(getattr(c, f)) for f in SHARED_FIELDS)
            if cur is None or score > sum(not _blank(getattr(cur, f)) for f in SHARED_FIELDS):
                reps[c.name] = c
    for g in items:
        rep = reps.get(g["name"])
        g["definition"] = {f: getattr(rep, f) for f in SHARED_FIELDS} if rep else {}
    return {"items": items, "total": len(groups), "page": page, "page_size": page_size}


@router.post("/column-groups/apply")
def apply_column_group(body: schemas.ColumnGroupApply, request: Request, session: Session = Db):
    patch = body.patch.model_dump(exclude_unset=True)
    if not patch:
        raise HTTPException(400, "Empty patch")
    stmt = (select(Column).join(Table, Table.id == Column.table_id)
            .where(Column.name == body.name, Column.removed.is_(False), Table.removed.is_(False)))
    if body.source_id:
        stmt = stmt.where(Table.source_id == body.source_id)
    if body.schema_name:
        stmt = stmt.where(Table.schema_name == body.schema_name)
    actor = actor_of(request)
    cols = session.scalars(stmt).all()
    updated, staged, tables = 0, 0, set()
    for c in cols:
        pend = revisions.pending_of(session, c.table) if c.table.status == "published" else None
        data = {}
        for field, value in patch.items():
            old = revisions.effective_value(c, pend, field)      # a staged value counts as "already filled"
            if body.only_empty and not _blank(old):
                continue
            data[field] = value
        if data:
            res = revisions.edit_column(session, c, data, actor)
            if res.total:
                updated += 1
                staged += bool(res.staged)
                tables.add(c.table_id)
    session.commit()
    return {"matched": len(cols), "updated": updated, "staged": staged, "tables": len(tables)}


# --------------------------------------------------------------------------- schemas
def _schema_out(s: SchemaMeta) -> dict:
    return {k: getattr(s, k) for k in s.__table__.columns.keys()}


@router.get("/schemas/{schema_id}")
def get_schema(schema_id: int, session: Session = Db):
    s = session.get(SchemaMeta, schema_id)
    if not s:
        raise HTTPException(404, "Schema not found")
    return _schema_out(s)


@router.patch("/schemas/{schema_id}")
def update_schema(schema_id: int, body: schemas.SchemaMetaUpdate, request: Request, session: Session = Db):
    s = session.get(SchemaMeta, schema_id)
    if not s:
        raise HTTPException(404, "Schema not found")
    actor = actor_of(request)
    for field, value in body.model_dump(exclude_unset=True).items():
        if getattr(s, field) != value:
            _audit(session, "schema", s, field, getattr(s, field), value, actor)
            setattr(s, field, value)
    session.commit()
    return _schema_out(s)


# --------------------------------------------------------------------------- CSV round-trip
def _kv(d: dict | None) -> str:
    return "|".join(f"{k}={v}" for k, v in (d or {}).items())


def _unkv(s: str) -> dict:
    return dict(p.split("=", 1) for p in s.split("|") if "=" in p)


def _csv_response(name: str, header: list[str], rows: list[list]) -> Response:
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(header)
    w.writerows(rows)
    # BOM so Excel opens Arabic text correctly
    return Response("﻿" + buf.getvalue(), media_type="text/csv; charset=utf-8",
                    headers={"Content-Disposition": f'attachment; filename="{name}"'})


COLUMN_CSV = ["source", "schema", "table", "column", "data_type", "display_name", "display_name_ar",
              "description", "description_ar", "role", "semantic_type", "unit", "default_aggregation",
              "synonyms", "synonyms_ar", "allowed_values", "allowed_values_ar", "is_primary_key", "pii"]
TABLE_CSV = ["source", "schema", "table", "display_name", "display_name_ar", "description",
             "description_ar", "grain", "grain_ar", "table_type", "domain", "owner", "status"]


@router.get("/export/columns.csv")
def export_columns(f: dict = Filters, session: Session = Db):
    ids = [r["id"] for r in table_rows(session, f)]
    out = []
    stmt = (select(Table).where(Table.id.in_(ids)).order_by(Table.schema_name, Table.name))
    for t in session.scalars(stmt):
        for c in t.columns:
            if c.removed:
                continue
            out.append([t.source.name, t.schema_name, t.name, c.name, c.data_type, c.display_name or "",
                        c.display_name_ar or "", c.description or "", c.description_ar or "", c.role or "",
                        c.semantic_type or "", c.unit or "", c.default_aggregation or "",
                        "|".join(c.synonyms or []), "|".join(c.synonyms_ar or []), _kv(c.allowed_values),
                        _kv(c.allowed_values_ar), int(c.is_primary_key), int(c.pii)])
    return _csv_response("columns.csv", COLUMN_CSV, out)


@router.get("/export/tables.csv")
def export_tables(f: dict = Filters, session: Session = Db):
    ids = [r["id"] for r in table_rows(session, f)]
    out = []
    for t in session.scalars(select(Table).where(Table.id.in_(ids)).order_by(Table.schema_name, Table.name)):
        out.append([t.source.name, t.schema_name, t.name, t.display_name or "", t.display_name_ar or "",
                    t.description or "", t.description_ar or "", t.grain or "", t.grain_ar or "",
                    t.table_type or "", t.domain or "", t.owner or "", t.status])
    return _csv_response("tables.csv", TABLE_CSV, out)


def _read_csv(raw: bytes) -> list[dict]:
    text = raw.decode("utf-8-sig")
    return list(csv.DictReader(io.StringIO(text)))


@router.post("/import/columns")
async def import_columns(request: Request, session: Session = Db):
    """Body: CSV as exported. Non-empty cells overwrite; empty cells leave the catalog unchanged."""
    rows = _read_csv(await request.body())
    actor = actor_of(request)
    sources = {s.name: s.id for s in session.scalars(select(Source))}
    updated, staged, errors = 0, 0, []
    lists = {"synonyms", "synonyms_ar"}
    kvs = {"allowed_values", "allowed_values_ar"}
    flags = {"is_primary_key", "pii"}
    plain = {"display_name", "display_name_ar", "description", "description_ar", "role", "semantic_type",
             "unit", "default_aggregation"}
    for i, r in enumerate(rows, start=2):
        sid = sources.get(r.get("source", ""))
        col = session.scalar(
            select(Column).join(Table, Table.id == Column.table_id)
            .where(Table.source_id == sid, Table.schema_name == r.get("schema"),
                   Table.name == r.get("table"), Column.name == r.get("column"))) if sid else None
        if col is None:
            errors.append(f"row {i}: {r.get('source')}.{r.get('schema')}.{r.get('table')}.{r.get('column')} not found")
            continue
        data = {}
        for field in plain | lists | kvs | flags:
            cell = (r.get(field) or "").strip()
            if cell:
                data[field] = (cell.split("|") if field in lists else _unkv(cell) if field in kvs
                               else cell in ("1", "true", "True", "yes") if field in flags else cell)
        res = revisions.edit_column(session, col, data, actor)
        updated += bool(res.total)
        staged += bool(res.staged)
    session.commit()
    return {"rows": len(rows), "updated": updated, "staged": staged, "errors": errors[:50]}


@router.post("/import/tables")
async def import_tables(request: Request, session: Session = Db):
    rows = _read_csv(await request.body())
    actor = actor_of(request)
    cfg = get_settings(session)
    sources = {s.name: s.id for s in session.scalars(select(Source))}
    fields = [f for f in TABLE_CSV if f not in ("source", "schema", "table", "status")]
    updated, staged, errors = 0, 0, []
    for i, r in enumerate(rows, start=2):
        sid = sources.get(r.get("source", ""))
        t = session.scalar(select(Table).where(Table.source_id == sid, Table.schema_name == r.get("schema"),
                                               Table.name == r.get("table"))) if sid else None
        if t is None:
            errors.append(f"row {i}: {r.get('source')}.{r.get('schema')}.{r.get('table')} not found")
            continue
        data = {("table_type" if f == "table_type" else f): (r.get(f) or "").strip() for f in fields if (r.get(f) or "").strip()}
        res = revisions.edit_table(session, t, data, actor)
        status = (r.get("status") or "").strip()
        moved = False
        if status and status != t.status:
            if status not in ("draft", "reviewed", "published"):
                errors.append(f"row {i}: invalid status {status!r}")
            else:
                problems = revisions.transition_status(session, t, status, actor, cfg=cfg, raise_on_block=False)
                if problems:
                    errors.append(f"row {i}: cannot publish {t.name}: " + "; ".join(problems))
                else:
                    moved = True
        updated += bool(res.live or moved or res.staged)
        staged += bool(res.staged)
    session.commit()
    return {"rows": len(rows), "updated": updated, "staged": staged, "errors": errors[:50]}


# --------------------------------------------------------------------------- quarantine
def _quarantine_query(f: dict):
    stmt = (select(Column, Table, Source.name)
            .join(Table, Table.id == Column.table_id).join(Source, Source.id == Table.source_id)
            .where(Column.quarantined.is_(True), Column.removed.is_(False), Table.removed.is_(False)))
    if f.get("source_id"):
        stmt = stmt.where(Table.source_id == int(f["source_id"]))
    if f.get("schema"):
        stmt = stmt.where(Table.schema_name == f["schema"])
    if f.get("reason") == "sensitive":
        stmt = stmt.where(Column.quarantine_reason.ilike("%sensitive%"))
    elif f.get("reason") == "new":
        stmt = stmt.where(Column.quarantine_reason.ilike("New column%"))
    return stmt


@router.get("/quarantine")
def quarantine(source_id: int | None = None, schema: str | None = None, reason: str | None = None,
               q: str | None = None, page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=200),
               session: Session = Db):
    """Columns hidden from agents until a steward reviews them."""
    f = {k: v for k, v in dict(source_id=source_id, schema=schema, reason=reason).items() if v}
    rows = []
    for c, t, src in session.execute(_quarantine_query(f).order_by(Source.name, Table.schema_name, Table.name, Column.ordinal)):
        if q and not i18n.hit(q, c.name, t.name, t.schema_name, src, c.quarantine_reason):
            continue
        rows.append({"id": c.id, "column": c.name, "data_type": c.data_type, "reason": c.quarantine_reason,
                     "table_id": t.id, "table": f"{src}.{t.schema_name}.{t.name}", "table_status": t.status,
                     "published": t.status == "published"})
    start = (page - 1) * page_size
    return {"items": rows[start:start + page_size], "total": len(rows), "page": page, "page_size": page_size}


class QuarantineRelease(BaseModel):
    ids: list[int] | None = None
    filters: dict | None = None
    mark_pii: bool = False        # also flag them as personal data (hidden or value-masked per the PII setting)


@router.post("/quarantine/release")
def quarantine_release(body: QuarantineRelease, request: Request, session: Session = Db):
    if body.ids is None and body.filters is None:
        raise HTTPException(400, "Provide ids or filters")
    actor = actor_of(request)
    if body.ids is not None:
        cols = session.scalars(select(Column).where(Column.id.in_(body.ids), Column.quarantined.is_(True))).all()
    else:
        cols = [row[0] for row in session.execute(_quarantine_query(body.filters or {}))]
    data = {"quarantined": False, "needs_review": False, **({"pii": True} if body.mark_pii else {})}
    n = sum(bool(revisions.edit_column(session, c, data, actor).total) for c in cols)
    session.commit()
    return {"released": n, "marked_pii": n if body.mark_pii else 0}


# --------------------------------------------------------------------------- pending revisions queue
@router.get("/revisions/pending")
def pending_revisions(source_id: int | None = None, schema: str | None = None, q: str | None = None,
                      page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=200), session: Session = Db):
    stmt = (select(TableRevision, Table, Source.name)
            .join(Table, Table.id == TableRevision.table_id).join(Source, Source.id == Table.source_id)
            .where(TableRevision.status == "pending", Table.removed.is_(False))
            .order_by(TableRevision.updated_at.desc()))
    if source_id:
        stmt = stmt.where(Table.source_id == source_id)
    if schema:
        stmt = stmt.where(Table.schema_name == schema)
    rows = []
    for rev, t, src in session.execute(stmt):
        if q and not i18n.hit(q, t.name, t.schema_name, src, t.display_name):
            continue
        summary = revisions.pending_summary(rev)
        rows.append({"table_id": t.id, "table": f"{src}.{t.schema_name}.{t.name}", "version": t.version,
                     "changes": summary["count"], "columns_touched": len(summary["column_fields"]),
                     "contributors": rev.contributors, "updated_at": rev.updated_at})
    start = (page - 1) * page_size
    return {"items": rows[start:start + page_size], "total": len(rows), "page": page, "page_size": page_size}


class RevisionBulk(BaseModel):
    table_ids: list[int] | None = None
    action: Literal["publish", "discard"]
    message: str | None = None


@router.post("/revisions/bulk")
def revisions_bulk(body: RevisionBulk, request: Request, session: Session = Db):
    """Publish or discard many pending revisions. Each is judged on its own; failures are reported, not fatal."""
    actor = actor_of(request)
    cfg = get_settings(session)
    ids = body.table_ids
    if ids is None:
        ids = list(session.scalars(select(TableRevision.table_id).where(TableRevision.status == "pending")))
    done, failed = 0, []
    for t in session.scalars(select(Table).where(Table.id.in_(ids))):
        try:
            if body.action == "publish":
                revisions.publish_pending(session, t, actor, body.message, cfg=cfg)
            else:
                revisions.discard_pending(session, t, actor)
            session.commit()
            done += 1
        except HTTPException as e:
            session.rollback()
            failed.append({"table": t.full_name, "reason": e.detail})
    return {"done": done, "failed": len(failed), "failed_examples": failed[:5]}
