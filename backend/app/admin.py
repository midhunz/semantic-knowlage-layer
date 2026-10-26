"""Admin settings API: global settings, API keys, users, webhooks, audit log. Admin-only."""

import secrets
from datetime import datetime, timedelta, timezone
from typing import Literal
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.auth import (MIN_PASSWORD, SCOPES, Principal, hash_password, new_api_key, require_admin,
                      user_out, users_exist)
from app.db import get_session
from app.models import ApiKey, AuditLog, Column, Dimension, Table, User, UserSession, Webhook
from app.services import settings_store, webhooks

router = APIRouter(prefix="/api/admin", tags=["admin"], dependencies=[Depends(require_admin)])
Db = Depends(get_session)

SCOPE_INFO = {
    "agent:read": "Read published tables, metrics and glossary (what chatbots and agents need).",
    "catalog:read": "Read the whole catalog, including drafts, through /api.",
    "catalog:write": "Edit the catalog through /api (e.g. a CI job that syncs or documents tables).",
}
ROLE_INFO = {
    "viewer": "Can browse the catalog. Cannot change anything.",
    "steward": "Can document tables and columns, publish, and run syncs.",
    "admin": "Everything a steward can do, plus settings, users, API keys and webhooks.",
}


def _now() -> datetime:
    return datetime.now(timezone.utc)


@router.get("/meta")
def meta():
    return {"scopes": [{"id": k, "description": v} for k, v in SCOPE_INFO.items()],
            "roles": [{"id": k, "description": v} for k, v in ROLE_INFO.items()],
            "events": [{"id": k, "description": v} for k, v in webhooks.EVENTS.items() if k != "webhook.test"],
            "min_password_length": MIN_PASSWORD}


# --------------------------------------------------------------------------- settings
class SettingsIn(BaseModel):
    org_name: str | None = Field(default=None, max_length=100)
    default_lang: Literal["en", "ar", "both"] | None = None
    default_max_tokens: int | None = Field(default=None, ge=0, le=200_000)
    pii_columns_in_agent_output: Literal["names_only", "exclude"] | None = None
    require_review_before_publish: bool | None = None
    min_completeness_to_publish: float | None = Field(default=None, ge=0, le=1)
    session_hours: int | None = Field(default=None, ge=1, le=720)
    pii_name_patterns: str | None = Field(default=None, max_length=2000)
    revision_requires_different_approver: bool | None = None
    mcp_enabled: bool | None = None
    mcp_disabled_tools: list[str] | None = None
    mcp_run_query_max_rows: int | None = Field(default=None, ge=1, le=1000)


def _mcp_tools() -> list[dict]:
    """The tools the MCP server really exposes, read from the server itself so this page cannot drift from the code."""
    import asyncio
    import re

    from app import mcp_server  # imported lazily: it imports app.main

    out = []
    for t in asyncio.run(mcp_server.mcp.list_tools()):
        text = re.sub(r"\s+", " ", (t.description or "").strip())
        first = re.split(r"(?<=[.!?])\s+(?=[A-Z“\"])|\s+lang:", text, maxsplit=1)[0]  # first sentence; not at "e.g. x" or a parameter note
        out.append({"name": t.name, "summary": first[:200], "access": "raw" if t.name in mcp_server.RAW_DATA_TOOLS else "catalog"})
    return out


@router.get("/mcp")
def mcp_info(session: Session = Db):
    from importlib.metadata import version

    cfg = settings_store.get_settings(session)
    return {"server": {"name": "semantic-layer", "transport": "stdio", "sdk_version": version("mcp"),
                       "command": "python -m app.mcp_server"},
            "tools": _mcp_tools(),
            "settings": {k: cfg[k] for k in ("mcp_enabled", "mcp_disabled_tools", "mcp_run_query_max_rows")}}


@router.get("/settings")
def get_settings(session: Session = Db):
    return settings_store.get_settings(session)


@router.put("/settings")
def put_settings(body: SettingsIn, session: Session = Db):
    if body.mcp_disabled_tools is not None:
        known = {t["name"] for t in _mcp_tools()}
        bad = sorted(set(body.mcp_disabled_tools) - known)
        if bad:
            raise HTTPException(422, f"Unknown MCP tool: {', '.join(bad)}")
    return settings_store.save_settings(session, body.model_dump(exclude_unset=True, exclude_none=True))


# --------------------------------------------------------------------------- api keys
class KeyIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    scopes: list[str] = ["agent:read"]
    allowed_domains: list[str] = []
    expires_in_days: int | None = Field(default=None, ge=1, le=3650)


class KeyPatch(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = None
    scopes: list[str] | None = None
    allowed_domains: list[str] | None = None


def _check_scopes(scopes: list[str]) -> list[str]:
    bad = [s for s in scopes if s not in SCOPES]
    if bad or not scopes:
        raise HTTPException(422, f"Choose at least one valid scope ({', '.join(SCOPES)})")
    return sorted(set(scopes))


def _key_out(k: ApiKey) -> dict:
    exp = k.expires_at.replace(tzinfo=timezone.utc) if k.expires_at and k.expires_at.tzinfo is None else k.expires_at
    status = "revoked" if k.revoked_at else "expired" if exp and exp < _now() else "active"
    return {"id": k.id, "name": k.name, "description": k.description, "prefix": k.key_prefix, "scopes": k.scopes,
            "allowed_domains": k.allowed_domains, "created_by": k.created_by, "created_at": k.created_at,
            "expires_at": k.expires_at, "last_used_at": k.last_used_at, "use_count": k.use_count,
            "status": status}


@router.get("/keys")
def list_keys(session: Session = Db):
    return [_key_out(k) for k in session.scalars(select(ApiKey).order_by(ApiKey.created_at.desc()))]


@router.post("/keys")
def create_key(body: KeyIn, p: Principal = Depends(require_admin), session: Session = Db):
    secret, prefix, digest = new_api_key()
    key = ApiKey(name=body.name.strip(), description=body.description, key_prefix=prefix, key_hash=digest,
                 scopes=_check_scopes(body.scopes),
                 allowed_domains=[d.strip() for d in body.allowed_domains if d.strip()],
                 created_by=p.label,
                 expires_at=_now() + timedelta(days=body.expires_in_days) if body.expires_in_days else None)
    session.add(key)
    session.commit()
    return {"key": _key_out(key), "secret": secret}  # the only time the secret is ever returned


def _key(session: Session, key_id: int) -> ApiKey:
    k = session.get(ApiKey, key_id)
    if k is None:
        raise HTTPException(404, "API key not found")
    return k


@router.patch("/keys/{key_id}")
def patch_key(key_id: int, body: KeyPatch, session: Session = Db):
    k = _key(session, key_id)
    data = body.model_dump(exclude_unset=True)
    if "scopes" in data:
        data["scopes"] = _check_scopes(data["scopes"] or [])
    if "allowed_domains" in data:
        data["allowed_domains"] = [d.strip() for d in data["allowed_domains"] or [] if d.strip()]
    for f, v in data.items():
        setattr(k, f, v)
    session.commit()
    return _key_out(k)


@router.post("/keys/{key_id}/revoke")
def revoke_key(key_id: int, session: Session = Db):
    k = _key(session, key_id)
    k.revoked_at = k.revoked_at or _now()
    session.commit()
    return _key_out(k)


@router.post("/keys/{key_id}/rotate")
def rotate_key(key_id: int, session: Session = Db):
    """Issue a new secret for the same key settings; the old secret stops working immediately."""
    k = _key(session, key_id)
    secret, prefix, digest = new_api_key()
    k.key_prefix, k.key_hash, k.revoked_at = prefix, digest, None
    session.commit()
    return {"key": _key_out(k), "secret": secret}


@router.delete("/keys/{key_id}")
def delete_key(key_id: int, session: Session = Db):
    session.delete(_key(session, key_id))
    session.commit()
    return {"deleted": key_id}


# --------------------------------------------------------------------------- users
class UserIn(BaseModel):
    email: str = Field(min_length=3, max_length=200, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    name: str = Field(default="", max_length=200)
    role: Literal["viewer", "steward", "admin"] = "viewer"
    password: str | None = Field(default=None, min_length=MIN_PASSWORD, max_length=200)


class UserPatch(BaseModel):
    name: str | None = Field(default=None, max_length=200)
    role: Literal["viewer", "steward", "admin"] | None = None
    is_active: bool | None = None


def _temp_password() -> str:
    return secrets.token_urlsafe(9)


def _user(session: Session, user_id: int) -> User:
    u = session.get(User, user_id)
    if u is None:
        raise HTTPException(404, "User not found")
    return u


def _active_admins(session: Session, excluding: int | None = None) -> int:
    q = select(func.count()).select_from(User).where(User.role == "admin", User.is_active.is_(True))
    if excluding is not None:
        q = q.where(User.id != excluding)
    return session.scalar(q) or 0


@router.get("/users")
def list_users(session: Session = Db):
    return [user_out(u) for u in session.scalars(select(User).order_by(User.email))]


@router.post("/users")
def create_user(body: UserIn, session: Session = Db):
    if not users_exist(session):
        raise HTTPException(409, "Create the first administrator with the setup form first")
    email = body.email.strip().lower()
    if session.scalar(select(User).where(User.email == email)):
        raise HTTPException(409, f"{email} already has an account")
    temp = None if body.password else _temp_password()
    u = User(email=email, name=body.name.strip(), role=body.role,
             password_hash=hash_password(body.password or temp), must_change_password=temp is not None)
    session.add(u)
    session.commit()
    return {"user": user_out(u), "temporary_password": temp}


@router.patch("/users/{user_id}")
def patch_user(user_id: int, body: UserPatch, p: Principal = Depends(require_admin), session: Session = Db):
    u = _user(session, user_id)
    data = body.model_dump(exclude_unset=True, exclude_none=True)
    losing_admin = u.role == "admin" and u.is_active and (
        data.get("role", "admin") != "admin" or data.get("is_active", True) is False)
    if losing_admin and _active_admins(session, excluding=u.id) == 0:
        raise HTTPException(409, "There must be at least one active administrator")
    if p.user and p.user.id == u.id and data.get("is_active") is False:
        raise HTTPException(409, "You cannot deactivate your own account")
    for f, v in data.items():
        setattr(u, f, v)
    if data.get("is_active") is False:
        session.query(UserSession).filter(UserSession.user_id == u.id).delete()
    session.commit()
    return user_out(u)


@router.post("/users/{user_id}/reset-password")
def reset_password(user_id: int, session: Session = Db):
    u = _user(session, user_id)
    temp = _temp_password()
    u.password_hash, u.must_change_password = hash_password(temp), True
    session.query(UserSession).filter(UserSession.user_id == u.id).delete()  # sign them out everywhere
    session.commit()
    return {"user": user_out(u), "temporary_password": temp}


@router.delete("/users/{user_id}")
def delete_user(user_id: int, p: Principal = Depends(require_admin), session: Session = Db):
    u = _user(session, user_id)
    if p.user and p.user.id == u.id:
        raise HTTPException(409, "You cannot delete your own account")
    if u.role == "admin" and u.is_active and _active_admins(session, excluding=u.id) == 0:
        raise HTTPException(409, "There must be at least one active administrator")
    session.query(UserSession).filter(UserSession.user_id == u.id).delete()
    session.delete(u)
    session.commit()
    return {"deleted": user_id}


# --------------------------------------------------------------------------- webhooks
class HookIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    url: str = Field(max_length=1000)
    events: list[str]
    is_active: bool = True


class HookPatch(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    url: str | None = Field(default=None, max_length=1000)
    events: list[str] | None = None
    is_active: bool | None = None


def _check_hook(url: str | None, events: list[str] | None) -> None:
    if url is not None:
        u = urlparse(url)
        if u.scheme not in ("http", "https") or not u.netloc:
            raise HTTPException(422, "URL must start with http:// or https://")
    if events is not None:
        bad = [e for e in events if e not in webhooks.EVENTS or e == "webhook.test"]
        if bad or not events:
            raise HTTPException(422, "Choose at least one valid event")


def _hook_out(h: Webhook) -> dict:
    return {"id": h.id, "name": h.name, "url": h.url, "events": h.events, "is_active": h.is_active,
            "secret_hint": "…" + h.secret[-4:], "last_delivery_at": h.last_delivery_at,
            "last_status": h.last_status, "created_at": h.created_at}


@router.get("/webhooks")
def list_hooks(session: Session = Db):
    return [_hook_out(h) for h in session.scalars(select(Webhook).order_by(Webhook.name))]


@router.post("/webhooks")
def create_hook(body: HookIn, session: Session = Db):
    _check_hook(body.url, body.events)
    h = Webhook(name=body.name.strip(), url=body.url.strip(), events=body.events, is_active=body.is_active,
                secret="whsec_" + secrets.token_urlsafe(24))
    session.add(h)
    session.commit()
    return {"webhook": _hook_out(h), "secret": h.secret}


def _hook(session: Session, hook_id: int) -> Webhook:
    h = session.get(Webhook, hook_id)
    if h is None:
        raise HTTPException(404, "Webhook not found")
    return h


@router.patch("/webhooks/{hook_id}")
def patch_hook(hook_id: int, body: HookPatch, session: Session = Db):
    h = _hook(session, hook_id)
    data = body.model_dump(exclude_unset=True)
    _check_hook(data.get("url"), data.get("events"))
    for f, v in data.items():
        setattr(h, f, v.strip() if isinstance(v, str) else v)
    session.commit()
    return _hook_out(h)


@router.post("/webhooks/{hook_id}/rotate-secret")
def rotate_hook_secret(hook_id: int, session: Session = Db):
    h = _hook(session, hook_id)
    h.secret = "whsec_" + secrets.token_urlsafe(24)
    session.commit()
    return {"webhook": _hook_out(h), "secret": h.secret}


@router.post("/webhooks/{hook_id}/test")
def test_hook(hook_id: int, session: Session = Db):
    h = _hook(session, hook_id)
    status = webhooks.deliver(h.url, h.secret, "webhook.test", {"message": "Hello from the semantic layer"})
    h.last_delivery_at, h.last_status = _now(), status
    session.commit()
    return {"status": status, "ok": status.startswith("2")}


@router.delete("/webhooks/{hook_id}")
def delete_hook(hook_id: int, session: Session = Db):
    session.delete(_hook(session, hook_id))
    session.commit()
    return {"deleted": hook_id}


# --------------------------------------------------------------------------- audit log
@router.get("/audit")
def audit(actor: str | None = None, entity: str | None = None, q: str | None = None,
          page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=200), session: Session = Db):
    stmt = select(AuditLog)
    if actor:
        stmt = stmt.where(AuditLog.actor == actor)
    if entity:
        stmt = stmt.where(AuditLog.entity == entity)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(AuditLog.field.ilike(like) | AuditLog.old_value.ilike(like)
                          | AuditLog.new_value.ilike(like))
    total = session.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = session.scalars(stmt.order_by(AuditLog.id.desc()).offset((page - 1) * page_size)
                           .limit(page_size)).all()
    tables = {t.id: t for t in session.scalars(select(Table).where(
        Table.id.in_([r.entity_id for r in rows if r.entity == "table"] or [-1])))}
    cols = {c.id: c for c in session.scalars(select(Column).where(
        Column.id.in_([r.entity_id for r in rows if r.entity == "column"] or [-1])))}

    dimensions = {d.id: d.key for d in session.scalars(select(Dimension).where(
        Dimension.id.in_([r.entity_id for r in rows if r.entity == "dimension"] or [-1])))}

    def label(r: AuditLog) -> str:
        if r.entity == "dimension":
            return f"dimension {dimensions.get(r.entity_id, '#' + str(r.entity_id))}"
        if r.entity == "table" and r.entity_id in tables:
            return tables[r.entity_id].full_name
        if r.entity == "column" and r.entity_id in cols:
            return f"{cols[r.entity_id].table.full_name}.{cols[r.entity_id].name}"
        return f"{r.entity} #{r.entity_id}"

    actors = [a for (a,) in session.execute(select(AuditLog.actor).distinct().order_by(AuditLog.actor))]
    return {"items": [{"id": r.id, "at": r.at, "actor": r.actor, "entity": r.entity, "target": label(r),
                       "field": r.field, "old": r.old_value, "new": r.new_value, "staged": r.staged} for r in rows],
            "total": total, "page": page, "page_size": page_size, "actors": actors}
