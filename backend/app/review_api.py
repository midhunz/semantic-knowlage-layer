"""Review queue: submit, approve or reject dimensions, metrics and glossary terms (/api/review)."""

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.auth import actor_of, catalog_access
from app.db import get_session
from app.services import review

router = APIRouter(prefix="/api/review", tags=["review"], dependencies=[Depends(catalog_access)])
Db = Depends(get_session)


class RejectBody(BaseModel):
    note: str = Field(max_length=1000)


@router.get("")
def queue(session: Session = Db):
    """Everything waiting for a reviewer, with what changed against the live version."""
    items = review.queue(session)
    return {"total": len(items), "items": items}


@router.post("/{kind}/{item_id}/edit-draft")
def edit_draft(kind: str, item_id: int, request: Request, session: Session = Db):
    """The item to edit: itself while it is not live, otherwise its draft copy (created on first use)."""
    target = review.start_draft(session, review.get(session, kind, item_id), actor_of(request))
    session.commit()
    return review.item_out(session, target)


@router.post("/{kind}/{item_id}/submit")
def submit(kind: str, item_id: int, request: Request, session: Session = Db):
    obj = review.get(session, kind, item_id)
    review.submit(session, obj, actor_of(request))
    session.commit()
    return review.item_out(session, obj)


@router.post("/{kind}/{item_id}/approve")
def approve(kind: str, item_id: int, request: Request, session: Session = Db):
    live = review.approve(session, review.get(session, kind, item_id), actor_of(request))
    session.commit()
    return review.item_out(session, live)


@router.post("/{kind}/{item_id}/reject")
def reject(kind: str, item_id: int, body: RejectBody, request: Request, session: Session = Db):
    obj = review.get(session, kind, item_id)
    review.reject(session, obj, actor_of(request), body.note)
    session.commit()
    return review.item_out(session, obj)


@router.post("/{kind}/{item_id}/unpublish")
def unpublish(kind: str, item_id: int, request: Request, session: Session = Db):
    obj = review.get(session, kind, item_id)
    review.unpublish(session, obj, actor_of(request))
    session.commit()
    return review.item_out(session, obj)


@router.delete("/{kind}/{item_id}/draft")
def discard(kind: str, item_id: int, request: Request, session: Session = Db):
    review.discard(session, review.get(session, kind, item_id), actor_of(request))
    session.commit()
    return {"discarded": True}
