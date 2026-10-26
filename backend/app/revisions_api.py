"""Per-table revision endpoints: see, publish or discard pending changes; browse and restore versions."""

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import actor_of, catalog_access
from app.db import get_session
from app.models import Table, TableRevision
from app.services import revisions

router = APIRouter(prefix="/api/tables", tags=["revisions"], dependencies=[Depends(catalog_access)])
Db = Depends(get_session)


def _table(session: Session, table_id: int) -> Table:
    t = session.get(Table, table_id)
    if t is None:
        raise HTTPException(404, f"Table {table_id} not found")
    return t


class PublishBody(BaseModel):
    message: str | None = Field(default=None, max_length=500)


class RestoreBody(BaseModel):
    replace: bool = False      # discard any pending changes and stage the restore instead


def _rev_out(r: TableRevision) -> dict:
    return {"number": r.number, "message": r.message, "published_by": r.published_by, "published_at": r.published_at,
            "created_by": r.created_by, "contributors": r.contributors, "changes": len(r.diff or [])}


@router.get("/{table_id}/revision")
def get_pending(table_id: int, session: Session = Db):
    """The pending working copy (if any) with its diff against what is live."""
    t = _table(session, table_id)
    pend = revisions.pending_of(session, t)
    return {"version": t.version, "pending": revisions.pending_summary(pend),
            "diff": revisions.pending_diff(t, pend) if pend else []}


@router.post("/{table_id}/revision/publish")
def publish_pending(table_id: int, body: PublishBody, request: Request, session: Session = Db):
    t = _table(session, table_id)
    rev = revisions.publish_pending(session, t, actor_of(request), body.message)
    session.commit()
    return {"version": rev.number, "changes": len(rev.diff)}


@router.delete("/{table_id}/revision")
def discard_pending(table_id: int, request: Request, session: Session = Db):
    t = _table(session, table_id)
    revisions.discard_pending(session, t, actor_of(request))
    session.commit()
    return {"discarded": True}


@router.get("/{table_id}/revisions")
def history(table_id: int, session: Session = Db):
    """Published versions, newest first."""
    t = _table(session, table_id)
    revs = session.scalars(select(TableRevision).where(TableRevision.table_id == t.id,
                                                       TableRevision.status == "published")
                           .order_by(TableRevision.number.desc())).all()
    return {"version": t.version, "items": [_rev_out(r) for r in revs]}


@router.get("/{table_id}/revisions/{number}")
def version_detail(table_id: int, number: int, session: Session = Db):
    """What one version changed, and what restoring it would change right now."""
    t = _table(session, table_id)
    rev = session.scalar(select(TableRevision).where(TableRevision.table_id == t.id,
                                                     TableRevision.status == "published",
                                                     TableRevision.number == number))
    if rev is None:
        raise HTTPException(404, f"Version {number} not found")
    return {**_rev_out(rev), "diff": rev.diff,
            "restore_preview": revisions.state_diff(revisions.live_state(t), rev.snapshot)}


@router.post("/{table_id}/revisions/{number}/restore")
def restore(table_id: int, number: int, body: RestoreBody, request: Request, session: Session = Db):
    t = _table(session, table_id)
    out = revisions.restore_version(session, t, number, actor_of(request), body.replace)
    session.commit()
    return out
