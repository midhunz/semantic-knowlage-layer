"""Dimensions: authoring API (/api/dimensions) and the agent-facing lookup (/agent/dimensions, /agent/resolve-value)."""

import json

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import i18n
from app.auth import Principal, actor_of, agent_access, catalog_access
from app.connectors import get_connector
from app.db import get_session
from app.models import Column, Dimension, DimensionBinding, DimensionValue, Table, _now
from app.services import dimensions as dims
from app.services import export, revisions, webhooks
from app.services.settings_store import get_settings

router = APIRouter(prefix="/api/dimensions", tags=["dimensions"], dependencies=[Depends(catalog_access)])
agent_router = APIRouter(prefix="/agent", tags=["agent"], dependencies=[Depends(agent_access)])
Db = Depends(get_session)

LOAD_LIMIT = 200


# --------------------------------------------------------------------------- request models
class Family(BaseModel):
    term: str = Field(min_length=1, max_length=120)
    term_ar: str | None = Field(default=None, max_length=120)
    values: list[str] = Field(default_factory=list, max_length=200)


class Condition(BaseModel):
    dimension: str = Field(min_length=1, max_length=64)
    values: list[str] = Field(default_factory=list, max_length=200)


class DimensionIn(BaseModel):
    key: str = Field(pattern=dims.KEY_RE.pattern)
    label: str | None = Field(default=None, max_length=200)
    label_ar: str | None = Field(default=None, max_length=200)
    description: str | None = None
    description_ar: str | None = None
    synonyms: list[str] = []
    synonyms_ar: list[str] = []


class DimensionPatch(BaseModel):
    label: str | None = Field(default=None, max_length=200)
    label_ar: str | None = Field(default=None, max_length=200)
    description: str | None = None
    description_ar: str | None = None
    synonyms: list[str] | None = None
    synonyms_ar: list[str] | None = None
    families: list[Family] | None = None
    applies_to: list[Condition] | None = None
    applies_note: str | None = None
    applies_note_ar: str | None = None
    status: str | None = Field(default=None, pattern="^(draft|published)$")


class ValueIn(BaseModel):
    value: str = Field(min_length=1, max_length=200)
    label: str | None = Field(default=None, max_length=200)
    label_ar: str | None = Field(default=None, max_length=200)
    aliases: list[str] = []


class ValuePatch(BaseModel):          # the stored value itself is immutable: other rules refer to it
    label: str | None = Field(default=None, max_length=200)
    label_ar: str | None = Field(default=None, max_length=200)
    aliases: list[str] | None = None
    position: int | None = None


class BulkValues(BaseModel):
    values: list[ValueIn] = Field(max_length=500)


class BindBody(BaseModel):
    column_ids: list[int] = Field(min_length=1, max_length=500)


class LoadBody(BaseModel):
    column_id: int | None = None


# --------------------------------------------------------------------------- helpers
def _dim(session: Session, dim_id: int) -> Dimension:
    d = session.get(Dimension, dim_id)
    if d is None:
        raise HTTPException(404, "Dimension not found")
    return d


def _value(dim: Dimension, value_id: int) -> DimensionValue:
    v = next((x for x in dim.values if x.id == value_id), None)
    if v is None:
        raise HTTPException(404, "Value not found")
    return v


def _blank(v):
    return None if v is None or (isinstance(v, str) and not v.strip()) else v


def _audit(session: Session, dim: Dimension, field: str, old, new, actor: str) -> None:
    revisions.audit(session, "dimension", dim, field, old, new, actor)


def _touch(session: Session, dim: Dimension, what: str) -> None:
    """Dimension edits are live, so tell downstream apps when a published one changes."""
    dim.updated_at = _now()
    if dim.status == "published":
        webhooks.emit(session, "dimension.updated", {"key": dim.key, "change": what})


def _fail_on_errors(session: Session, dim: Dimension) -> None:
    session.flush()
    session.refresh(dim)
    errs = dims.errors(dims.check(session, dim))
    if errs:
        session.rollback()
        raise HTTPException(422, "; ".join(e["message"] for e in errs))


def _value_out(v: DimensionValue) -> dict:
    return {"id": v.id, "value": v.value, "label": v.label, "label_ar": v.label_ar, "aliases": v.aliases or [],
            "position": v.position}


def _binding_out(b: DimensionBinding) -> dict:
    c, t = b.column, b.column.table
    return {"column_id": c.id, "column": c.name, "data_type": c.data_type, "table_id": t.id, "table": t.full_name,
            "table_status": t.status, "dropped": c.removed or t.removed, "hidden": c.quarantined, "pii": c.pii}


def _summary(session: Session, d: Dimension) -> dict:
    issues = dims.check(session, d)
    return {"id": d.id, "key": d.key, "label": d.label, "label_ar": d.label_ar, "status": d.status,
            "values": len(d.values), "bindings": len(d.bindings), "families": len(d.families or []),
            "applies": bool(d.applies_to), "errors": len(dims.errors(issues)),
            "warnings": len(issues) - len(dims.errors(issues)), "updated_at": d.updated_at}


def _detail(session: Session, d: Dimension) -> dict:
    return {**_summary(session, d), "description": d.description, "description_ar": d.description_ar,
            "synonyms": d.synonyms or [], "synonyms_ar": d.synonyms_ar or [], "families": d.families or [],
            "applies_to": d.applies_to or [], "applies_note": d.applies_note, "applies_note_ar": d.applies_note_ar,
            "values_list": [_value_out(v) for v in d.values], "bindings_list": [_binding_out(b) for b in d.bindings],
            "issues": dims.check(session, d),
            "applies_preview": dims.applies_doc(session, d, "both")}


# --------------------------------------------------------------------------- dimensions
@router.get("")
def list_dimensions(q: str | None = None, status: str | None = None, session: Session = Db):
    out = []
    for d in session.scalars(select(Dimension).order_by(Dimension.key)):
        if status and d.status != status:
            continue
        if q and not i18n.hit(q, d.key, d.label, d.label_ar, d.synonyms or [], d.synonyms_ar or [],
                              [v.value for v in d.values]):
            continue
        out.append(_summary(session, d))
    return out


@router.post("")
def create_dimension(body: DimensionIn, request: Request, session: Session = Db):
    if session.scalar(select(Dimension).where(Dimension.key == body.key)):
        raise HTTPException(409, f"A dimension with the key “{body.key}” already exists")
    d = Dimension(key=body.key, label=_blank(body.label), label_ar=_blank(body.label_ar),
                  description=_blank(body.description), description_ar=_blank(body.description_ar),
                  synonyms=dims.clean_words(body.synonyms), synonyms_ar=dims.clean_words(body.synonyms_ar))
    session.add(d)
    session.flush()
    _audit(session, d, "created", None, body.key, actor_of(request))
    session.commit()
    return _detail(session, d)


@router.get("/columns")
def search_columns(q: str = "", dimension_id: int | None = None, limit: int = Query(40, ge=1, le=200),
                   session: Session = Db):
    """Columns that could be bound to a dimension (for the "bind columns" picker)."""
    stmt = (select(Column, Table).join(Table, Table.id == Column.table_id)
            .where(Column.removed.is_(False), Table.removed.is_(False)).order_by(Column.name, Table.name))
    bound = {b.column_id: b.dimension.key for b in session.scalars(select(DimensionBinding))}
    out = []
    for c, t in session.execute(stmt):
        if q and not i18n.hit(q, c.name, t.name, t.schema_name, t.source.name):
            continue
        out.append({"id": c.id, "column": c.name, "data_type": c.data_type, "table": t.full_name, "pii": c.pii,
                    "hidden": c.quarantined, "bound_to": bound.get(c.id)})
        if len(out) >= limit:
            break
    return out


@router.get("/{dim_id}")
def get_dimension(dim_id: int, session: Session = Db):
    return _detail(session, _dim(session, dim_id))


@router.patch("/{dim_id}")
def update_dimension(dim_id: int, body: DimensionPatch, request: Request, session: Session = Db):
    d = _dim(session, dim_id)
    actor = actor_of(request)
    data = body.model_dump(exclude_unset=True)
    status = data.pop("status", None)
    changed = []
    for field, new in data.items():
        if field in ("synonyms", "synonyms_ar"):
            new = dims.clean_words(new)
        elif field == "families":
            new = [{"term": f["term"].strip(), "term_ar": _blank(f.get("term_ar")),
                    "values": list(dict.fromkeys(f["values"]))} for f in new]
        elif field == "applies_to":
            new = [{"dimension": c["dimension"], "values": list(dict.fromkeys(c["values"]))} for c in new]
        else:
            new = _blank(new)
        old = getattr(d, field)
        if old != new and not (not old and not new):
            _audit(session, d, field, old, new, actor)
            setattr(d, field, new)
            changed.append(field)
    if changed:
        _fail_on_errors(session, d)
    if status and status != d.status:
        if status == "published":
            errs = dims.errors(dims.check(session, d))
            if errs:
                raise HTTPException(422, "Cannot publish: " + "; ".join(e["message"] for e in errs))
        _audit(session, d, "status", d.status, status, actor)
        d.status = status
        changed.append("status")
    if changed:
        _touch(session, d, ", ".join(changed))
    session.commit()
    return _detail(session, d)


@router.delete("/{dim_id}")
def delete_dimension(dim_id: int, request: Request, session: Session = Db):
    d = _dim(session, dim_id)
    users = [o.key for o in session.scalars(select(Dimension)) if o.id != d.id
             and any(c.get("dimension") == d.key for c in o.applies_to or [])]
    if users:
        raise HTTPException(409, f"Other dimensions restrict themselves by {d.key}: {', '.join(users)}. Change those first.")
    _audit(session, d, "deleted", d.key, None, actor_of(request))
    if d.status == "published":
        webhooks.emit(session, "dimension.updated", {"key": d.key, "change": "deleted"})
    session.delete(d)
    session.commit()
    return {"deleted": dim_id}


# --------------------------------------------------------------------------- values
def _add_value(session: Session, d: Dimension, body: ValueIn) -> DimensionValue | None:
    value = body.value.strip()
    if not value or any(v.value == value for v in d.values):
        return None
    v = DimensionValue(dimension_id=d.id, value=value, label=_blank(body.label), label_ar=_blank(body.label_ar),
                       aliases=dims.clean_words(body.aliases), position=len(d.values))
    d.values.append(v)
    return v


@router.post("/{dim_id}/values")
def add_value(dim_id: int, body: ValueIn, request: Request, session: Session = Db):
    d = _dim(session, dim_id)
    if not body.value.strip():
        raise HTTPException(422, "A value is required")
    v = _add_value(session, d, body)
    if v is None:
        raise HTTPException(409, f"“{body.value.strip()}” is already a value of {d.key}")
    session.flush()
    _audit(session, d, f"value {v.value}", None, json.dumps(_value_out(v), ensure_ascii=False), actor_of(request))
    _touch(session, d, f"added value {v.value}")
    session.commit()
    return _detail(session, d)


@router.post("/{dim_id}/values/bulk")
def add_values(dim_id: int, body: BulkValues, request: Request, session: Session = Db):
    d = _dim(session, dim_id)
    added = [v for v in (_add_value(session, d, b) for b in body.values) if v]
    session.flush()
    if added:
        _audit(session, d, "values", None, f"added {len(added)}: " + ", ".join(v.value for v in added[:20]), actor_of(request))
        _touch(session, d, f"added {len(added)} values")
    session.commit()
    return {"added": len(added), "skipped": len(body.values) - len(added), "dimension": _detail(session, d)}


@router.patch("/{dim_id}/values/{value_id}")
def update_value(dim_id: int, value_id: int, body: ValuePatch, request: Request, session: Session = Db):
    d = _dim(session, dim_id)
    v = _value(d, value_id)
    actor = actor_of(request)
    for field, new in body.model_dump(exclude_unset=True).items():
        new = dims.clean_words(new) if field == "aliases" else (_blank(new) if field != "position" else new)
        old = getattr(v, field)
        if old != new:
            _audit(session, d, f"value {v.value}: {field}", old, new, actor)
            setattr(v, field, new)
    _touch(session, d, f"edited value {v.value}")
    session.commit()
    return _detail(session, d)


@router.get("/{dim_id}/values/{value_id}/dependents")
def value_dependents(dim_id: int, value_id: int, session: Session = Db):
    d = _dim(session, dim_id)
    v = _value(d, value_id)
    dep = dims.value_dependents(session, d, v.value)
    return {**dep, "blocking": bool(dep["applies_to"])}


@router.delete("/{dim_id}/values/{value_id}")
def delete_value(dim_id: int, value_id: int, request: Request, confirm: bool = False, session: Session = Db):
    d = _dim(session, dim_id)
    v = _value(d, value_id)
    dep = dims.value_dependents(session, d, v.value)
    if dep["applies_to"]:      # these change reported numbers, so they must be edited deliberately first
        who = ", ".join(a["dimension"] for a in dep["applies_to"])
        raise HTTPException(409, f"“{v.value}” is used by the “applies to” rule of {who}. Change that rule first.")
    if (dep["families"] or dep["aliases"]) and not confirm:
        bits = ([f"{dep['aliases']} alias(es)"] if dep["aliases"] else []) + (
            [f"the families {', '.join(dep['families'])}"] if dep["families"] else [])
        raise HTTPException(409, f"Removing “{v.value}” also removes {' and '.join(bits)}. Confirm to continue.")
    dropped, fams = [], []            # remove it from families; a family left with one value is dropped
    for f in d.families or []:
        vals = [x for x in f.get("values") or [] if x != v.value]
        if len(vals) == len(f.get("values") or []):
            fams.append(f)
        elif len(vals) >= 2:
            fams.append({**f, "values": vals})
        else:
            dropped.append(f.get("term"))
    d.families = fams
    _audit(session, d, f"value {v.value}", json.dumps(_value_out(v), ensure_ascii=False), None, actor_of(request))
    d.values.remove(v)
    _touch(session, d, f"removed value {v.value}")
    session.commit()
    return {"removed": v.value, "families_dropped": dropped, "dimension": _detail(session, d)}


# --------------------------------------------------------------------------- bindings
@router.post("/{dim_id}/bindings")
def bind_columns(dim_id: int, body: BindBody, request: Request, session: Session = Db):
    d = _dim(session, dim_id)
    actor = actor_of(request)
    existing = {b.column_id: b.dimension.key for b in session.scalars(select(DimensionBinding))}
    added = 0
    for cid in dict.fromkeys(body.column_ids):
        col = session.get(Column, cid)
        if col is None:
            raise HTTPException(404, f"Column {cid} not found")
        if existing.get(cid) == d.key:
            continue
        if cid in existing:
            raise HTTPException(409, f"{col.table.full_name}.{col.name} already belongs to the dimension “{existing[cid]}”")
        d.bindings.append(DimensionBinding(column_id=cid))
        _audit(session, d, "bound column", None, f"{col.table.full_name}.{col.name}", actor)
        added += 1
    if added:
        _touch(session, d, f"bound {added} column(s)")
    session.commit()
    return _detail(session, d)


@router.delete("/{dim_id}/bindings/{column_id}")
def unbind_column(dim_id: int, column_id: int, request: Request, session: Session = Db):
    d = _dim(session, dim_id)
    b = next((x for x in d.bindings if x.column_id == column_id), None)
    if b is None:
        raise HTTPException(404, "That column is not bound to this dimension")
    _audit(session, d, "unbound column", f"{b.column.table.full_name}.{b.column.name}", None, actor_of(request))
    d.bindings.remove(b)
    _touch(session, d, "unbound a column")
    session.commit()
    return _detail(session, d)


@router.get("/{dim_id}/validation")
def validation(dim_id: int, session: Session = Db):
    return {"issues": dims.check(session, _dim(session, dim_id))}


# --------------------------------------------------------------------------- load values from the data
@router.post("/{dim_id}/load-values")
def load_values(dim_id: int, body: LoadBody, session: Session = Db):
    """Read the real distinct values of the bound columns from the lake. Nothing is saved: the caller picks
    which to add. Columns holding personal data, or hidden for review, are never read."""
    d = _dim(session, dim_id)
    bindings = [b for b in d.bindings if body.column_id in (None, b.column_id)]
    if not bindings:
        raise HTTPException(400, "Bind at least one column first")
    known = {v.value for v in d.values}
    found: dict[str, dict] = {}
    errors, skipped, truncated, connectors = [], [], False, {}
    read_ok = 0
    for b in bindings:
        c, t = b.column, b.column.table
        name = f"{t.full_name}.{c.name}"
        if c.removed or t.removed:
            skipped.append({"column": name, "reason": "dropped from the lake"})
        elif c.pii:
            skipped.append({"column": name, "reason": "marked as personal data — its values are never read"})
        elif c.quarantined:
            skipped.append({"column": name, "reason": "hidden for review — release it first"})
        else:
            try:
                if t.source_id not in connectors:
                    connectors[t.source_id] = get_connector(t.source.kind, t.source.config)
                res = connectors[t.source_id].distinct_values(t.schema_name, t.name, c.name, LOAD_LIMIT)
            except Exception as e:  # noqa: BLE001  (a lake being down must not look like a server bug)
                errors.append({"column": name, "error": f"{type(e).__name__}: {e}"[:300]})
                continue
            read_ok += 1
            truncated = truncated or res["truncated"]
            for value, n in res["values"]:
                row = found.setdefault(value, {"value": value, "count": 0, "columns": [], "in_vocabulary": value in known})
                row["count"] += n
                row["columns"].append(name)
    values = sorted(found.values(), key=lambda r: (-r["count"], r["value"]))
    complete = read_ok == len([b for b in bindings if b.column.pii is False]) and not truncated and not errors
    return {"values": values, "truncated": truncated, "errors": errors, "skipped": skipped,
            "missing_from_data": sorted(known - set(found)) if complete and read_ok else [],
            "sampled": "Counts come from a sample of the table, not a full scan."}


# --------------------------------------------------------------------------- agent-facing
def _domains(p: Principal) -> list | None:
    return p.domains


@agent_router.get("/dimensions")
def agent_dimensions(lang: str | None = None, full: bool = False, format: str = "json", max_tokens: int | None = None,
                     p: Principal = Depends(agent_access), session: Session = Db):
    """Published dimensions. `full=true&format=yaml` returns every dimension with its whole vocabulary as text."""
    cfg = get_settings(session)
    lang = lang or cfg["default_lang"]
    visible = dims.visible_dimensions(session, _domains(p))
    if not full:
        return [dims.dimension_summary(d, lang) for d in visible]
    from fastapi.responses import PlainTextResponse
    body = export.render([dims.dimension_doc(session, d, lang) for d in visible], format,
                         max_tokens or cfg["default_max_tokens"] or None)
    return PlainTextResponse(body, media_type="application/json" if format == "json" else "text/yaml")


@agent_router.get("/dimensions/{key}")
def agent_dimension(key: str, lang: str | None = None, p: Principal = Depends(agent_access), session: Session = Db):
    lang = lang or get_settings(session)["default_lang"]
    d = next((x for x in dims.visible_dimensions(session, _domains(p)) if x.key == key), None)
    if d is None:
        raise HTTPException(404, f"No published dimension {key}")
    return dims.dimension_doc(session, d, lang)


@agent_router.get("/resolve-value")
def agent_resolve_value(text: str, dimension: str | None = None, lang: str | None = None,
                        p: Principal = Depends(agent_access), session: Session = Db):
    """Map a word someone used ("residents", "مقيمين") to the value stored in the data."""
    lang = lang or get_settings(session)["default_lang"]
    return dims.resolve(dims.visible_dimensions(session, _domains(p)), text, dimension, lang)
