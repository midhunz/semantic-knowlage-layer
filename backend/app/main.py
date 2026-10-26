from fastapi import APIRouter, Depends, FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from sqlalchemy import delete, func, or_, select, update
from sqlalchemy.orm import Session

from app import admin as admin_api
from app import catalog, dimensions_api, i18n, revisions_api, schemas
from app.auth import Principal, actor_of, agent_access, catalog_access
from app.auth import router as auth_router
from app.connectors import get_connector
from app.config import settings
from app.db import get_session
from app.models import (AuditLog, Column, DimensionBinding, GlossaryTerm, Metric, Profile, Relationship, SampleQuery,
                        SchemaMeta, Source, Table)
from app.services import export, revisions, webhooks
from app.services.settings_store import get_settings
from app.services.sync import apply_sync, completeness, load_source
from app.web import install, lifespan, serve_ui

app = FastAPI(title="Semantic Knowledge Layer", lifespan=lifespan,
              # the interactive API docs list every endpoint: off in production unless SL_ENABLE_DOCS=true
              docs_url="/docs" if settings.docs_enabled else None,
              redoc_url=None, openapi_url="/openapi.json" if settings.docs_enabled else None)
if settings.cors_origin_list:
    app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origin_list, allow_credentials=True,
                       allow_methods=["*"], allow_headers=["*"])
install(app)

Db = Depends(get_session)
admin = APIRouter(prefix="/api", tags=["catalog"], dependencies=[Depends(catalog_access)])
agent = APIRouter(prefix="/agent", tags=["agent"], dependencies=[Depends(agent_access)])


def _get(session: Session, model, id_: int):
    obj = session.get(model, id_)
    if obj is None:
        raise HTTPException(404, f"{model.__name__} {id_} not found")
    return obj


# ---------- sources & sync ----------
def _source_out(session: Session, src: Source) -> dict:
    tables = session.scalars(select(Table).where(Table.source_id == src.id, Table.removed.is_(False))).all()
    return {"id": src.id, "name": src.name, "kind": src.kind, "config": src.config,
            "last_synced_at": src.last_synced_at, "tables": len(tables),
            "published": sum(t.status == "published" for t in tables)}


def _unique_name(session: Session, name: str, exclude_id: int | None = None) -> None:
    other = session.scalar(select(Source).where(Source.name == name))
    if other and other.id != exclude_id:
        raise HTTPException(409, f"A source named '{name}' already exists")


def _connect(src_kind: str, config: dict):
    try:
        return get_connector(src_kind, config)
    except KeyError as e:
        raise HTTPException(400, f"Missing connection setting: {e}")
    except Exception as e:
        raise HTTPException(502, f"Could not connect: {e}")


@admin.post("/sources")
def create_source(body: schemas.SourceIn, session: Session = Db):
    _unique_name(session, body.name)
    src = Source(**body.model_dump())
    session.add(src)
    session.commit()
    return _source_out(session, src)


@admin.get("/sources")
def list_sources(session: Session = Db):
    return [_source_out(session, s) for s in session.scalars(select(Source).order_by(Source.name))]


@admin.put("/sources/{source_id}")
def update_source(source_id: int, body: schemas.SourceIn, session: Session = Db):
    src = _get(session, Source, source_id)
    _unique_name(session, body.name, exclude_id=src.id)
    src.name, src.kind, src.config = body.name, body.kind, body.config
    session.commit()
    return _source_out(session, src)


@admin.post("/sources/test")
def test_connection(body: schemas.SourceIn):
    """Check credentials/reachability without saving anything."""
    conn = _connect(body.kind, body.config)
    try:
        return {"ok": True, "detail": conn.ping()}
    except Exception as e:
        raise HTTPException(502, f"Connection test failed: {e}")


@admin.get("/sources/{source_id}/impact")
def source_impact(source_id: int, session: Session = Db):
    """What deleting this source would remove — shown before the user confirms."""
    src = _get(session, Source, source_id)
    cols = [c for t in src.tables for c in t.columns]
    return {
        "name": src.name, "tables": len(src.tables), "columns": len(cols),
        "published_tables": sum(t.status == "published" for t in src.tables),
        "curated_tables": sum(bool(t.description or t.description_ar or t.grain) for t in src.tables),
        "curated_columns": sum(bool(c.description or c.description_ar) for c in cols),
        "metrics": session.scalar(select(func.count()).select_from(Metric).where(
            Metric.base_table_id.in_([t.id for t in src.tables] or [-1]))),
    }


@admin.delete("/sources/{source_id}")
def delete_source(source_id: int, session: Session = Db):
    """Delete the source and everything curated under it (tables, columns, joins, profiles)."""
    src = load_source(session, source_id)
    if src is None:
        raise HTTPException(404, f"Source {source_id} not found")
    table_ids = [t.id for t in src.tables]
    col_ids = [c.id for t in src.tables for c in t.columns]
    if col_ids:
        session.execute(delete(Relationship).where(or_(Relationship.from_column_id.in_(col_ids),
                                                       Relationship.to_column_id.in_(col_ids))))
        session.execute(delete(Profile).where(Profile.column_id.in_(col_ids)))
        session.execute(delete(DimensionBinding).where(DimensionBinding.column_id.in_(col_ids)))
    if table_ids:  # keep metrics, just detach them from the removed tables
        session.execute(update(Metric).where(Metric.base_table_id.in_(table_ids)).values(base_table_id=None))
    session.execute(delete(SchemaMeta).where(SchemaMeta.source_id == src.id))
    name, n = src.name, len(table_ids)
    session.delete(src)
    session.commit()
    return {"deleted": name, "tables_removed": n}


@admin.post("/sources/{source_id}/sync")
def sync_source(source_id: int, schemas_: list[str] | None = Query(default=None, alias="schema"),
                session: Session = Db):
    src = load_source(session, source_id)
    if src is None:
        raise HTTPException(404, f"Source {source_id} not found")
    conn = _connect(src.kind, src.config)
    try:
        discovered = conn.introspect(schemas_)
    except Exception as e:
        raise HTTPException(502, f"Sync failed: {e}")
    stats = apply_sync(session, src, discovered, scope=schemas_)
    webhooks.emit(session, "catalog.synced", {"source": src.name, "schemas": schemas_ or "all", **stats})
    return stats


@admin.post("/columns/{column_id}/profile")
def profile_column(column_id: int, session: Session = Db):
    col = _get(session, Column, column_id)
    src = col.table.source
    result = get_connector(src.kind, src.config).profile_column(col.table.schema_name,
                                                                col.table.name, col.name)
    prof = session.scalar(select(Profile).where(Profile.column_id == col.id)) or Profile(column_id=col.id)
    for k, v in result.items():
        setattr(prof, k, v)
    session.add(prof)
    session.commit()
    return result


# ---------- tables & columns ----------
def _table_summary(t: Table) -> dict:
    return {"id": t.id, "fqn": t.fqn, "type": t.table_type, "domain": t.domain, "status": t.status,
            "description": t.description, "needs_review": t.needs_review, "removed": t.removed,
            "completeness": completeness(t)}


@admin.get("/tables")
def list_tables(status: str | None = None, needs_review: bool | None = None, session: Session = Db):
    q = select(Table).order_by(Table.schema_name, Table.name)
    if status:
        q = q.where(Table.status == status)
    if needs_review is not None:
        q = q.where(Table.needs_review == needs_review)
    return [_table_summary(t) for t in session.scalars(q)]


@admin.get("/tables/{table_id}")
def get_table(table_id: int, session: Session = Db):
    """The table as an editor should see it: live content with any pending (unpublished) changes laid over it."""
    t = _get(session, Table, table_id)
    pend = revisions.pending_of(session, t)
    state = revisions.merged_state(t, pend)
    bound = {b.column_id: b.dimension for b in session.scalars(
        select(DimensionBinding).where(DimensionBinding.column_id.in_([c.id for c in t.columns] or [-1])))}
    staged_cols = (pend.changes.get("columns", {}) if pend else {})
    cols = []
    for c in t.columns:
        d = {k: getattr(c, k) for k in c.__table__.columns.keys()}
        d.update(state["columns"][c.name])
        d["staged_fields"] = sorted(staged_cols.get(c.name, {}))
        dim = bound.get(c.id)
        d["dimension"] = {"id": dim.id, "key": dim.key, "label": dim.label or dim.key, "status": dim.status} if dim else None
        cols.append(d)
    out = {k: getattr(t, k) for k in t.__table__.columns.keys()}
    out.update(state["table"])
    return {**out, "fqn": t.fqn, "full_name": t.full_name, "source": t.source.name,
            "completeness": completeness(t), "completeness_ar": completeness(t, "ar"),
            "pending": revisions.pending_summary(pend), "columns": cols,
            "quarantined_count": sum(1 for c in t.columns if c.quarantined and not c.removed)}


@admin.patch("/tables/{table_id}")
def update_table(table_id: int, body: schemas.TableUpdate, request: Request, session: Session = Db):
    """Semantic edits to a *published* table are staged (see services/revisions.py); everything else is live."""
    t = _get(session, Table, table_id)
    actor = actor_of(request)
    data = body.model_dump(exclude_unset=True)
    status = data.pop("status", None)
    res = revisions.edit_table(session, t, data, actor)      # judged on the status the table has right now
    if status is not None:
        revisions.transition_status(session, t, status, actor)
    session.commit()
    return {**_table_summary(t), "staged": res.staged, "applied": res.live, "version": t.version}


@admin.patch("/columns/{column_id}")
def update_column(column_id: int, body: schemas.ColumnUpdate, request: Request, session: Session = Db):
    c = _get(session, Column, column_id)
    res = revisions.edit_column(session, c, body.model_dump(exclude_unset=True), actor_of(request))
    session.commit()
    return {**{k: getattr(c, k) for k in c.__table__.columns.keys()}, "staged": res.staged, "applied": res.live}


@admin.get("/audit")
def audit(entity: str | None = None, entity_id: int | None = None, session: Session = Db):
    q = select(AuditLog).order_by(AuditLog.id.desc()).limit(200)
    if entity:
        q = q.where(AuditLog.entity == entity)
    if entity_id is not None:
        q = q.where(AuditLog.entity_id == entity_id)
    return [{k: getattr(a, k) for k in a.__table__.columns.keys()} for a in session.scalars(q)]


# ---------- relationships / metrics / glossary / samples ----------
@admin.post("/relationships")
def create_relationship(body: schemas.RelationshipIn, session: Session = Db):
    _get(session, Column, body.from_column_id), _get(session, Column, body.to_column_id)
    r = Relationship(**body.model_dump())
    session.add(r)
    session.commit()
    return {"id": r.id}


def _crud(path: str, model, schema_in):
    @admin.post(f"/{path}", name=f"create_{path}")
    def create(body: schema_in, session: Session = Db):  # type: ignore[valid-type]
        obj = model(**body.model_dump())
        session.add(obj)
        session.commit()
        return {k: getattr(obj, k) for k in obj.__table__.columns.keys()}

    @admin.get(f"/{path}", name=f"list_{path}")
    def list_(session: Session = Db):
        return [{k: getattr(o, k) for k in o.__table__.columns.keys()} for o in session.scalars(select(model))]

    @admin.put(f"/{path}/{{item_id}}", name=f"update_{path}")
    def update(item_id: int, body: schema_in, session: Session = Db):  # type: ignore[valid-type]
        obj = _get(session, model, item_id)
        for k, v in body.model_dump().items():
            setattr(obj, k, v)
        session.commit()
        return {k: getattr(obj, k) for k in obj.__table__.columns.keys()}

    @admin.delete(f"/{path}/{{item_id}}", name=f"delete_{path}")
    def delete(item_id: int, session: Session = Db):
        session.delete(_get(session, model, item_id))
        session.commit()
        return {"deleted": item_id}


_crud("metrics", Metric, schemas.MetricIn)
_crud("glossary", GlossaryTerm, schemas.GlossaryIn)
_crud("sample-queries", SampleQuery, schemas.SampleQueryIn)


# ---------- agent-facing (published content only) ----------
def _published_table_by_fqn(session: Session, name: str, domains: list | None = None) -> Table:
    """Accepts `source.schema.table`, or `schema.table` when that is unambiguous across sources."""
    parts = name.split(".")
    q = select(Table).join(Source, Source.id == Table.source_id).where(
        Table.status == "published", Table.removed.is_(False))
    if len(parts) == 3:
        q = q.where(Source.name == parts[0], Table.schema_name == parts[1], Table.name == parts[2])
    elif len(parts) == 2:
        q = q.where(Table.schema_name == parts[0], Table.name == parts[1])
    else:
        raise HTTPException(400, "Use source.schema.table")
    if domains is not None:  # restricted API key: only its domains exist as far as it is concerned
        q = q.where(Table.domain.in_(domains))
    found = session.scalars(q).all()
    if not found:
        raise HTTPException(404, f"No published table {name}")
    if len(found) > 1:
        raise HTTPException(409, f"{name} is ambiguous across sources: "
                                 + ", ".join(t.full_name for t in found))
    return found[0]


def search_catalog(session: Session, q: str, limit: int = 20, lang: str | None = None,
                   domains: list | None = None) -> list[dict]:
    """Keyword search over published tables, columns (incl. synonyms) and metrics, in EN and AR."""
    lang = i18n.check_lang(lang or get_settings(session)["default_lang"])
    hits: list[dict] = []
    tables = select(Table).where(Table.status == "published", Table.removed.is_(False))
    if domains is not None:
        tables = tables.where(Table.domain.in_(domains))
    for t in session.scalars(tables):
        cols = [c for c in t.columns if not c.removed and not c.quarantined and i18n.hit(
            q, c.name, c.display_name, c.display_name_ar, c.description, c.description_ar,
            c.synonyms or [], c.synonyms_ar or [])]
        if cols or i18n.hit(q, t.name, t.display_name, t.display_name_ar, t.description, t.description_ar,
                            t.grain, t.grain_ar):
            hit: dict = {"table": t.full_name}
            i18n.put(hit, "description", t.description, t.description_ar, lang)
            hit["matching_columns"] = [c.name for c in cols]
            hits.append(hit)
    for m in _visible_metrics(session, domains):
        if i18n.hit(q, m.name, m.name_ar, m.description, m.description_ar, m.synonyms or [], m.synonyms_ar or []):
            hit = {"metric": m.name}
            i18n.put(hit, "description", m.description, m.description_ar, lang)
            hits.append(hit)
    return hits[:limit]


def _visible_metrics(session: Session, domains: list | None) -> list[Metric]:
    """Published metrics; a domain-restricted key only sees metrics whose base table is in its domains."""
    metrics = session.scalars(select(Metric).where(Metric.status == "published")).all()
    if domains is None:
        return list(metrics)
    allowed = {t.id for t in session.scalars(select(Table).where(Table.domain.in_(domains)))}
    return [m for m in metrics if m.base_table_id in allowed]


def _text(body: str, fmt: str) -> PlainTextResponse:
    return PlainTextResponse(body, media_type="application/json" if fmt == "json" else "text/yaml")


@agent.get("/search")
def agent_search(q: str, lang: str | None = None, p: Principal = Depends(agent_access), session: Session = Db):
    return search_catalog(session, q, lang=lang, domains=p.domains)


@agent.get("/tables/{fqn}/context")
def table_context(fqn: str, format: str = "yaml", lang: str | None = None, max_tokens: int | None = None,
                  p: Principal = Depends(agent_access), session: Session = Db):
    cfg = get_settings(session)
    doc = export.table_context(session, _published_table_by_fqn(session, fqn, p.domains),
                               lang or cfg["default_lang"], cfg)
    return _text(export.render([doc], format, max_tokens or cfg["default_max_tokens"] or None), format)


@agent.get("/export")
def export_all(domain: str | None = None, format: str = "yaml", lang: str | None = None,
               max_tokens: int | None = None, p: Principal = Depends(agent_access), session: Session = Db):
    cfg = get_settings(session)
    tables = export.published_tables(session, domain)
    if p.domains is not None:
        tables = [t for t in tables if t.domain in p.domains]
    docs = [export.table_context(session, t, lang or cfg["default_lang"], cfg) for t in tables]
    return _text(export.render(docs, format, max_tokens or cfg["default_max_tokens"] or None), format)


@agent.get("/glossary/resolve")
def resolve_term(term: str, lang: str | None = None, p: Principal = Depends(agent_access), session: Session = Db):
    lang = lang or get_settings(session)["default_lang"]
    out = []
    for t in export.glossary_resolve(session, term):
        item: dict = {"term": t.term}
        i18n.put(item, "definition", t.definition, t.definition_ar, lang)
        if t.term_ar:
            item["term_ar"] = t.term_ar
        item["links"] = t.links
        out.append(item)
    return out


@agent.get("/metrics")
def agent_metrics(lang: str | None = None, p: Principal = Depends(agent_access), session: Session = Db):
    lang = lang or get_settings(session)["default_lang"]
    out = []
    for m in _visible_metrics(session, p.domains):
        item: dict = {"name": m.name}
        if m.name_ar:
            item["name_ar"] = m.name_ar
        i18n.put(item, "description", m.description, m.description_ar, lang)
        item.update(sql=m.sql_expression, filters=m.filters,
                    synonyms=[*(m.synonyms or []), *(m.synonyms_ar or [])])
        out.append(item)
    return out


@agent.get("/sample-queries")
def agent_samples(p: Principal = Depends(agent_access), session: Session = Db):
    samples = session.scalars(select(SampleQuery).where(SampleQuery.verified.is_(True))).all()
    if p.domains is not None:  # keep only samples that touch nothing outside the key's domains
        ok = set()
        for t in session.scalars(select(Table).where(Table.status == "published", Table.domain.in_(p.domains))):
            ok |= {t.full_name, t.fqn}
        samples = [s for s in samples if s.tables and all(x in ok for x in s.tables)]
    return [{"question": s.question, "sql": s.sql, "tables": s.tables} for s in samples]


app.include_router(auth_router)
app.include_router(admin_api.router)
app.include_router(admin)
app.include_router(revisions_api.router)
app.include_router(dimensions_api.router)
app.include_router(dimensions_api.agent_router)
app.include_router(catalog.router, dependencies=[Depends(catalog_access)])
app.include_router(agent)
serve_ui(app)  # must stay last: its catch-all route only applies after every API route
