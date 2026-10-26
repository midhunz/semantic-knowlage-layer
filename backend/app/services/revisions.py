"""Staged edits for published tables.

Rules
-----
* A **published** table is what agents read. Edits to its *semantic* fields do not go live: they are saved
  in one pending revision ("working copy"). A steward reviews the diff and publishes it, which bumps the
  table's version. Agents always read the live rows, never the pending copy.
* Drafts (not published) are edited directly: nobody is reading them.
* Some changes are not content and stay live: status, review flags, quarantine, and *tightening* a safety
  flag (marking a column PII takes effect at once — delaying it would be wrong).
* Unpublishing a table folds its pending revision in (nobody is reading it any more).
* Every published version stores a full snapshot, so any version can be compared and restored.
"""

import json
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AuditLog, Column, Table, TableRevision
from app.services import webhooks
from app.services.policy import publish_blockers, revision_blockers
from app.services.settings_store import get_settings

TABLE_FIELDS = ("display_name", "display_name_ar", "description", "description_ar", "grain", "grain_ar",
                "table_type", "domain", "owner", "refresh_cadence", "usage_notes", "usage_notes_ar",
                "caveats", "caveats_ar", "pii_level", "certified")
COLUMN_FIELDS = ("display_name", "display_name_ar", "description", "description_ar", "role", "semantic_type",
                 "unit", "default_aggregation", "non_additive", "allowed_values", "allowed_values_ar",
                 "example_values", "format", "synonyms", "synonyms_ar", "is_primary_key", "pii", "deprecated")
LIVE_TABLE_FIELDS = ("status", "needs_review")
LIVE_COLUMN_FIELDS = ("needs_review", "quarantined", "quarantine_reason")


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _empty(v) -> bool:
    return v is None or v == "" or v == [] or v == {} or v is False


def _norm(v):
    return None if v == "" else v


def _same(a, b) -> bool:
    return (_empty(a) and _empty(b)) or a == b


def _text(v) -> str | None:
    """Audit values: readable for text, JSON for structures (so a rollback can parse them)."""
    if v is None or isinstance(v, str):
        return v
    return json.dumps(v, ensure_ascii=False)


def audit(session: Session, entity: str, obj, field: str, old, new, actor: str, staged: bool = False) -> None:
    session.add(AuditLog(entity=entity, entity_id=obj.id, field=field, actor=actor, staged=staged,
                         old_value=_text(old), new_value=_text(new)))


@dataclass
class EditResult:
    live: int = 0
    staged: int = 0

    @property
    def total(self) -> int:
        return self.live + self.staged

    def __iadd__(self, other: "EditResult") -> "EditResult":
        self.live += other.live
        self.staged += other.staged
        return self


# --------------------------------------------------------------------------- states and diffs
def live_state(table: Table) -> dict:
    return {"table": {f: _norm(getattr(table, f)) for f in TABLE_FIELDS},
            "columns": {c.name: {f: _norm(getattr(c, f)) for f in COLUMN_FIELDS} for c in table.columns}}


def pending_of(session: Session, table: Table) -> TableRevision | None:
    return session.scalar(select(TableRevision).where(TableRevision.table_id == table.id,
                                                      TableRevision.status == "pending"))


def latest_published(session: Session, table: Table) -> TableRevision | None:
    return session.scalar(select(TableRevision).where(TableRevision.table_id == table.id,
                                                      TableRevision.status == "published")
                          .order_by(TableRevision.number.desc()).limit(1))


def merged_state(table: Table, pending: TableRevision | None) -> dict:
    """What the editor shows: live content with the pending changes laid over it."""
    st = live_state(table)
    if pending:
        st["table"].update(pending.changes.get("table", {}))
        for name, ch in pending.changes.get("columns", {}).items():
            if name in st["columns"]:
                st["columns"][name].update(ch)
    return st


def state_diff(old: dict, new: dict) -> list[dict]:
    out = []
    for f in TABLE_FIELDS:
        a, b = old["table"].get(f), new["table"].get(f)
        if not _same(a, b):
            out.append({"scope": "table", "column": None, "field": f, "old": a, "new": b})
    for name, cols in new["columns"].items():
        before = old["columns"].get(name, {})
        for f in COLUMN_FIELDS:
            a, b = before.get(f), cols.get(f)
            if not _same(a, b):
                out.append({"scope": "column", "column": name, "field": f, "old": a, "new": b})
    return out


def pending_diff(table: Table, pending: TableRevision) -> list[dict]:
    return state_diff(live_state(table), merged_state(table, pending))


def pending_summary(pending: TableRevision | None) -> dict | None:
    if pending is None:
        return None
    cols = pending.changes.get("columns", {})
    tbl = pending.changes.get("table", {})
    return {"count": len(tbl) + sum(len(v) for v in cols.values()),
            "table_fields": sorted(tbl), "column_fields": {k: sorted(v) for k, v in cols.items()},
            "contributors": pending.contributors, "created_by": pending.created_by,
            "created_at": pending.created_at, "updated_at": pending.updated_at}


# --------------------------------------------------------------------------- versions
def _next_number(session: Session, table: Table) -> int:
    last = latest_published(session, table)
    return (last.number if last else 0) + 1


def ensure_baseline(session: Session, table: Table, actor: str = "system",
                    message: str = "Baseline before staged editing") -> None:
    """Make sure version 1 exists, so there is always something to diff against and restore."""
    if latest_published(session, table) is None:
        session.add(TableRevision(table_id=table.id, number=1, status="published", snapshot=live_state(table),
                                  diff=[], message=message, created_by=actor, contributors=[actor],
                                  published_by=actor, published_at=_now()))
        table.version = 1
        session.flush()


def record_publication(session: Session, table: Table, actor: str) -> None:
    """Called when a table becomes published: record a version if its content changed since the last one."""
    last = latest_published(session, table)
    snap = live_state(table)
    if last is None:
        number, diff, msg = 1, [], "Published"
    elif last.snapshot != snap:
        number, diff, msg = last.number + 1, state_diff(last.snapshot, snap), "Re-published with edits made while it was unpublished"
    else:
        return
    session.add(TableRevision(table_id=table.id, number=number, status="published", snapshot=snap, diff=diff,
                              message=msg, created_by=actor, contributors=[actor], published_by=actor,
                              published_at=_now()))
    table.version = number
    session.flush()


# --------------------------------------------------------------------------- editing
def _finalize(session: Session, table: Table, pend: TableRevision | None, changes: dict, actor: str) -> None:
    empty = not changes["table"] and not any(changes["columns"].values())
    if empty:
        if pend is not None:
            session.delete(pend)
            session.flush()
        return
    changes["columns"] = {k: v for k, v in changes["columns"].items() if v}
    if pend is None:
        ensure_baseline(session, table)
        pend = TableRevision(table_id=table.id, status="pending", created_by=actor, contributors=[],
                             changes=changes)
        session.add(pend)
    pend.changes = changes
    pend.updated_at = _now()
    if actor not in (pend.contributors or []):
        pend.contributors = [*(pend.contributors or []), actor]
    session.flush()


def _stage(changes: dict, scope: str, name: str | None, field: str, live_value, new) -> bool:
    """Put `new` into the pending changes (or drop the entry when it equals the live value)."""
    bucket = changes["table"] if scope == "table" else changes["columns"].setdefault(name, {})
    if _same(new, live_value):
        return bucket.pop(field, None) is not None
    if field in bucket and _same(bucket[field], new):
        return False
    bucket[field] = new
    return True


def edit_table(session: Session, table: Table, data: dict, actor: str) -> EditResult:
    """Apply semantic/review field edits to a table, staging them if it is published. Does not commit."""
    res = EditResult()
    staging = table.status == "published"
    pend = pending_of(session, table) if staging else None
    changes = deepcopy(pend.changes) if pend else {"table": {}, "columns": {}}
    changes.setdefault("table", {})
    changes.setdefault("columns", {})
    for field, raw in data.items():
        new = _norm(raw)
        if field in LIVE_TABLE_FIELDS or not staging:
            if field in TABLE_FIELDS or field in LIVE_TABLE_FIELDS:
                old = getattr(table, field)
                if not _same(old, new):
                    audit(session, "table", table, field, old, new, actor)
                    setattr(table, field, new)
                    res.live += 1
        elif field in TABLE_FIELDS:
            effective = changes["table"].get(field, getattr(table, field))
            if _stage(changes, "table", None, field, _norm(getattr(table, field)), new):
                audit(session, "table", table, field, effective, new, actor, staged=True)
                res.staged += 1
    if staging:
        _finalize(session, table, pend, changes, actor)
    return res


def edit_column(session: Session, col: Column, data: dict, actor: str) -> EditResult:
    """Apply semantic/review/quarantine edits to a column, staging semantic ones on published tables."""
    res = EditResult()
    table = col.table
    staging = table.status == "published"
    pend = pending_of(session, table) if staging else None
    changes = deepcopy(pend.changes) if pend else {"table": {}, "columns": {}}
    changes.setdefault("table", {})
    changes.setdefault("columns", {})
    touched = False
    for field, raw in data.items():
        new = _norm(raw)
        old_live = getattr(col, field, None)
        tightening = field == "pii" and bool(new) and not old_live        # safety goes live at once
        if field in LIVE_COLUMN_FIELDS or tightening or not staging:
            if field in COLUMN_FIELDS or field in LIVE_COLUMN_FIELDS:
                if not _same(old_live, new):
                    audit(session, "column", col, field, old_live, new, actor)
                    setattr(col, field, new)
                    res.live += 1
                    if field == "quarantined":     # releasing clears the reason; holding keeps or sets one
                        col.quarantine_reason = (col.quarantine_reason or f"Held by {actor}") if new else None
                    if tightening and staging:   # a staged "pii: false" would now be stale
                        changes["columns"].get(col.name, {}).pop("pii", None)
                        touched = True
        elif field in COLUMN_FIELDS:
            effective = changes["columns"].get(col.name, {}).get(field, old_live)
            if _stage(changes, "column", col.name, field, _norm(old_live), new):
                audit(session, "column", col, field, effective, new, actor, staged=True)
                res.staged += 1
                touched = True
    if staging and (res.staged or touched):
        _finalize(session, table, pend, changes, actor)
    return res


def effective_value(col: Column, pend: TableRevision | None, field: str):
    """The value a person editing this column sees: pending over live."""
    if pend:
        ch = pend.changes.get("columns", {}).get(col.name, {})
        if field in ch:
            return ch[field]
    return getattr(col, field)


# --------------------------------------------------------------------------- publishing a revision
def publish_pending(session: Session, table: Table, actor: str, message: str | None = None, *,
                    enforce: bool = True, cfg: dict | None = None) -> TableRevision:
    pend = pending_of(session, table)
    if pend is None:
        raise HTTPException(404, "This table has no pending changes")
    cfg = cfg or get_settings(session)
    if enforce:
        if cfg["revision_requires_different_approver"] and actor in (pend.contributors or []):
            raise HTTPException(403, "A different steward must approve changes you made yourself")
        problems = revision_blockers(session, table, merged_state(table, pend), cfg)
        if problems:
            raise HTTPException(422, f"Cannot publish these changes: " + "; ".join(problems))
    ensure_baseline(session, table)
    before = live_state(table)
    for f, v in pend.changes.get("table", {}).items():
        setattr(table, f, v)
    cols = {c.name: c for c in table.columns}
    for name, ch in pend.changes.get("columns", {}).items():
        if name in cols:                      # a column dropped from the lake meanwhile is skipped
            for f, v in ch.items():
                setattr(cols[name], f, v)
    after = live_state(table)
    last = latest_published(session, table)
    number = (last.number if last else 0) + 1
    pend.status, pend.number, pend.snapshot = "published", number, after
    pend.diff, pend.published_by, pend.published_at = state_diff(before, after), actor, _now()
    pend.message = (message or "").strip() or pend.message
    table.version = number
    audit(session, "table", table, "version", f"v{last.number}" if last else None, f"v{number}", actor)
    session.flush()
    webhooks.emit(session, "table.updated", {"table": table.full_name, "id": table.id, "version": number,
                                             "changes": len(pend.diff)})
    return pend


def discard_pending(session: Session, table: Table, actor: str) -> None:
    pend = pending_of(session, table)
    if pend is None:
        raise HTTPException(404, "This table has no pending changes")
    audit(session, "table", table, "revision", "pending", "discarded", actor)
    session.delete(pend)
    session.flush()


def restore_version(session: Session, table: Table, number: int, actor: str, replace: bool = False) -> dict:
    """Bring version `number` back. On a published table it is staged for review; on a draft it applies."""
    rev = session.scalar(select(TableRevision).where(TableRevision.table_id == table.id,
                                                     TableRevision.status == "published",
                                                     TableRevision.number == number))
    if rev is None:
        raise HTTPException(404, f"Version {number} not found")
    cur, target = live_state(table), rev.snapshot
    data_t = {f: target["table"].get(f) for f in TABLE_FIELDS if not _same(cur["table"].get(f), target["table"].get(f))}
    cols = {c.name: c for c in table.columns}
    if table.status == "published":
        pend = pending_of(session, table)
        if pend and not replace:
            raise HTTPException(409, "There are already pending changes. Publish or discard them first, or replace them.")
        if pend:
            session.delete(pend)
            session.flush()
    res = EditResult()
    if data_t:
        res += edit_table(session, table, data_t, actor)
    for name, vals in target["columns"].items():
        if name in cols:
            data_c = {f: vals.get(f) for f in COLUMN_FIELDS if not _same(cur["columns"].get(name, {}).get(f), vals.get(f))}
            if data_c:
                res += edit_column(session, cols[name], data_c, actor)
    if res.total == 0:
        raise HTTPException(409, f"Version {number} already matches the current content")
    pend = pending_of(session, table)
    if pend and res.staged:
        pend.message = f"Restore of v{number}"
    return {"staged": res.staged, "applied": res.live, "from_version": number}


# --------------------------------------------------------------------------- status changes
def transition_status(session: Session, table: Table, new_status: str, actor: str, *, cfg: dict | None = None,
                      raise_on_block: bool = True) -> list[str]:
    """Move a table between draft / reviewed / published, keeping versions and webhooks consistent."""
    old = table.status
    if new_status == old:
        return []
    cfg = cfg or get_settings(session)
    if new_status == "published":
        problems = publish_blockers(session, table, cfg)
        if problems:
            if raise_on_block:
                raise HTTPException(422, f"Cannot publish {table.fqn}: " + "; ".join(problems))
            return problems
    if old == "published" and pending_of(session, table):
        # nobody reads it any more, so the staged edits are applied (and versioned) rather than left dangling
        publish_pending(session, table, actor, "Applied when the table was unpublished", enforce=False, cfg=cfg)
    audit(session, "table", table, "status", old, new_status, actor)
    table.status = new_status
    if new_status == "published":
        record_publication(session, table, actor)
        webhooks.emit(session, "table.published", {"table": table.full_name, "id": table.id, "version": table.version})
    elif old == "published":
        webhooks.emit(session, "table.unpublished", {"table": table.full_name, "id": table.id})
    return []
