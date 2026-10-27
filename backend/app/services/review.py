"""Draft → review → published for dimensions, metrics and glossary terms.

Rules
-----
* Anything created starts as a **draft**. A steward *submits* it for review; a reviewer *approves* it
  (it goes live) or *rejects* it (back to draft, with a note).
* Agents only read **published** rows. A published item is never edited in place: the first edit creates one
  *draft copy* (`draft_of_id` → the live row). The copy follows draft → review → approve/reject; approving
  copies its content over the live row, rejecting returns it to draft, discarding deletes it.
* Editing an item that is in review sends it back to draft.
"""

from copy import deepcopy
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Dimension, DimensionBinding, DimensionValue, GlossaryTerm, Metric
from app.services import dimensions as dim_svc
from app.services import revisions, webhooks
from app.services.settings_store import get_settings

KINDS = {"dimension": Dimension, "metric": Metric, "glossary": GlossaryTerm}
NAME_FIELD = {"dimension": "key", "metric": "name", "glossary": "term"}
SKIP = {"id", "status", "draft_of_id", "review_note", "submitted_by", "submitted_at", "created_at", "updated_at"}
VALUE_FIELDS = ("value", "label", "label_ar", "aliases", "position")


def _now() -> datetime:
    return datetime.now(timezone.utc)


def kind_of(obj) -> str:
    return next(k for k, cls in KINDS.items() if isinstance(obj, cls))


def name_of(obj) -> str:
    return getattr(obj, NAME_FIELD[kind_of(obj)])


def get(session: Session, kind: str, item_id: int):
    cls = KINDS.get(kind)
    obj = session.get(cls, item_id) if cls else None
    if obj is None:
        raise HTTPException(404, f"{kind} {item_id} not found")
    return obj


def fields_of(obj) -> list[str]:
    return [c.key for c in obj.__table__.columns if c.key not in SKIP]


def draft_of(session: Session, live) -> object | None:
    return session.scalar(select(type(live)).where(type(live).draft_of_id == live.id))


def live_of(session: Session, obj):
    return session.get(type(obj), obj.draft_of_id) if obj.draft_of_id else None


def _audit(session: Session, obj, field: str, old, new, actor: str) -> None:
    live = live_of(session, obj) or obj
    revisions.audit(session, kind_of(obj), live, field, old, new, actor)


# --------------------------------------------------------------------------- editing
def for_edit(obj) -> None:
    """Call before changing an item. Published items are read-only (edit their draft copy instead)."""
    if obj.status == "published":
        raise HTTPException(409, "This item is live. Start a draft to change it; agents keep seeing the live "
                                 "version until a reviewer approves the draft.")
    if obj.status == "review":
        obj.status, obj.submitted_by, obj.submitted_at = "draft", None, None


def _clone_values(src: Dimension, dst: Dimension) -> None:
    dst.values = [DimensionValue(**{f: deepcopy(getattr(v, f)) for f in VALUE_FIELDS}) for v in src.values]
    dst.bindings = [DimensionBinding(column_id=b.column_id) for b in src.bindings]


def start_draft(session: Session, live, actor: str):
    """The draft copy of a published item (created on first use)."""
    if live.draft_of_id:
        raise HTTPException(409, "This already is a draft copy")
    if live.status != "published":
        return live                                   # not live yet: edit it directly
    copy = draft_of(session, live)
    if copy is not None:
        return copy
    copy = type(live)(**{f: deepcopy(getattr(live, f)) for f in fields_of(live)}, status="draft", draft_of_id=live.id)
    if isinstance(live, Dimension):
        _clone_values(live, copy)
    session.add(copy)
    session.flush()
    _audit(session, copy, "draft", None, "started", actor)
    return copy


def discard(session: Session, copy, actor: str) -> None:
    if not copy.draft_of_id:
        raise HTTPException(409, "Only a draft copy of a live item can be discarded")
    _audit(session, copy, "draft", "discarded", None, actor)
    session.delete(copy)
    session.flush()


def unpublish(session: Session, obj, actor: str) -> None:
    """Withdraw a live item from agents at once (taking something away is not a change that needs review)."""
    if obj.status != "published":
        raise HTTPException(409, "Only a live item can be withdrawn")
    obj.status, obj.submitted_by, obj.submitted_at = "draft", None, None
    _audit(session, obj, "status", "published", "draft", actor)
    _announce(session, obj, "withdrawn")


def delete_copies(session: Session, live) -> None:
    for c in session.scalars(select(type(live)).where(type(live).draft_of_id == live.id)).all():
        session.delete(c)


# --------------------------------------------------------------------------- the three transitions
def _problems(session: Session, obj) -> list[str]:
    if isinstance(obj, Dimension):
        return [e["message"] for e in dim_svc.errors(dim_svc.check(session, obj))]
    return []


def submit(session: Session, obj, actor: str) -> None:
    if obj.status != "draft":
        raise HTTPException(409, "Only a draft can be submitted for review")
    problems = _problems(session, obj)
    if problems:
        raise HTTPException(422, "Cannot submit: " + "; ".join(problems))
    obj.status, obj.submitted_by, obj.submitted_at, obj.review_note = "review", actor, _now(), None
    _audit(session, obj, "status", "draft", "review", actor)


def reject(session: Session, obj, actor: str, note: str) -> None:
    if obj.status != "review":
        raise HTTPException(409, "Only an item in review can be rejected")
    note = (note or "").strip()
    if not note:
        raise HTTPException(422, "Say why it is rejected so the author can fix it")
    obj.status, obj.review_note = "draft", note
    _audit(session, obj, "status", "review", f"rejected: {note}", actor)


def approve(session: Session, obj, actor: str):
    """Put the item live. Returns the live row (for a draft copy, the row it was a copy of)."""
    if obj.status != "review":
        raise HTTPException(409, "Only an item in review can be approved")
    if get_settings(session)["revision_requires_different_approver"] and actor == obj.submitted_by:
        raise HTTPException(403, "A different steward must approve what you submitted")
    problems = _problems(session, obj)
    if problems:
        raise HTTPException(422, "Cannot approve: " + "; ".join(problems))
    live = live_of(session, obj)
    if live is None:
        obj.status, obj.review_note = "published", None
        _audit(session, obj, "status", "review", "published", actor)
        _announce(session, obj, "published")
        return obj
    if isinstance(obj, Dimension):
        _check_bindings(session, obj)
    for f in fields_of(obj):
        setattr(live, f, deepcopy(getattr(obj, f)))
    if isinstance(obj, Dimension):
        live.values.clear()
        live.bindings.clear()
        session.flush()                               # free the old rows before inserting the same values again
        _clone_values(obj, live)
    if hasattr(live, "updated_at"):
        live.updated_at = _now()
    _audit(session, obj, "status", "review", "approved (draft copy went live)", actor)
    session.delete(obj)
    session.flush()
    _announce(session, live, "updated")
    return live


def _check_bindings(session: Session, copy: Dimension) -> None:
    taken = {b.column_id: b.dimension.key for b in session.scalars(
        select(DimensionBinding).join(Dimension, Dimension.id == DimensionBinding.dimension_id)
        .where(Dimension.draft_of_id.is_(None)))}
    for b in copy.bindings:
        if taken.get(b.column_id) not in (None, copy.key):
            raise HTTPException(409, f"{b.column.table.full_name}.{b.column.name} now belongs to the dimension "
                                     f"“{taken[b.column_id]}”. Unbind it from this draft first.")


def _announce(session: Session, live, change: str) -> None:
    kind = kind_of(live)
    webhooks.emit(session, f"{kind}.updated", {kind if kind != "dimension" else "key": name_of(live), "change": change})


# --------------------------------------------------------------------------- what a reviewer sees
def diff(session: Session, obj) -> dict:
    """Old → new for an item in review (against its live row, or "new" when it was never live)."""
    live = live_of(session, obj)
    out: dict = {"new": live is None, "fields": [], "values": {}, "bindings": {}}
    for f in fields_of(obj):
        old, new = getattr(live, f) if live else None, getattr(obj, f)
        if (old or None) != (new or None) and not (not old and not new):
            out["fields"].append({"field": f, "old": old, "new": new})
    if isinstance(obj, Dimension):
        before = {v.value: v for v in live.values} if live else {}
        after = {v.value: v for v in obj.values}
        out["values"] = {
            "added": [v for v in after if v not in before],
            "removed": [v for v in before if v not in after],
            "changed": [v for v in after if v in before
                        and any(getattr(after[v], f) != getattr(before[v], f) for f in VALUE_FIELDS if f != "position")]}
        b0 = {b.column_id for b in live.bindings} if live else set()
        label = {b.column_id: f"{b.column.table.full_name}.{b.column.name}" for d in (obj, live) if d for b in d.bindings}
        b1 = {b.column_id for b in obj.bindings}
        out["bindings"] = {"added": sorted(label[c] for c in b1 - b0), "removed": sorted(label[c] for c in b0 - b1)}
    return out


def item_out(session: Session, obj) -> dict:
    return {"kind": kind_of(obj), "id": obj.id, "name": name_of(obj), "live_id": obj.draft_of_id,
            "status": obj.status, "submitted_by": obj.submitted_by, "submitted_at": obj.submitted_at,
            "review_note": obj.review_note}


def queue(session: Session) -> list[dict]:
    out = []
    for cls in KINDS.values():
        for o in session.scalars(select(cls).where(cls.status == "review")):
            out.append({**item_out(session, o), "diff": diff(session, o)})
    return sorted(out, key=lambda r: r["submitted_at"] or _now())
