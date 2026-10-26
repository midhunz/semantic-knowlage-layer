"""Authentication & authorisation.

Open mode: until the first user exists the catalog is open (as it was before accounts existed) and the UI
nags the operator to create an admin. Once a user exists, every /api and /agent call needs either a
session cookie (people) or an API key (applications).
"""

import hashlib
import hmac
import os
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.config import settings as env_settings
from app.db import get_session
from app.models import ApiKey, LoginAttempt, User, UserSession
from app.services.settings_store import get_settings

ROLES = ("viewer", "steward", "admin")
RANK = {"viewer": 1, "steward": 2, "admin": 3}
SCOPES = ("agent:read", "catalog:read", "catalog:write")
COOKIE = "sl_session"
MIN_PASSWORD = 8


# --------------------------------------------------------------------------- secrets
def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1, dklen=32)
    return f"scrypt${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        _, salt, digest = stored.split("$")
        got = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt), n=2**14, r=8, p=1, dklen=32)
        return hmac.compare_digest(got.hex(), digest)
    except ValueError:
        return False


def sha256(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def new_api_key() -> tuple[str, str, str]:
    """(secret, display prefix, hash). The secret is shown once and never stored."""
    secret = "sl_live_" + secrets.token_urlsafe(32)
    return secret, secret[:15], sha256(secret)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _aware(dt: datetime | None) -> datetime | None:
    return dt.replace(tzinfo=timezone.utc) if dt is not None and dt.tzinfo is None else dt


# --------------------------------------------------------------------------- principals
@dataclass
class Principal:
    kind: str                   # user | key | legacy | anon
    label: str                  # recorded as the actor in the audit log
    rank: int                   # 0 none, 1 viewer, 2 steward, 3 admin
    scopes: frozenset
    domains: list | None = None  # None = every domain
    user: User | None = None
    key: ApiKey | None = None


def users_exist(session: Session) -> bool:
    return (session.scalar(select(func.count()).select_from(User)) or 0) > 0


def _presented_key(request: Request) -> str | None:
    key = request.headers.get("x-api-key")
    auth = request.headers.get("authorization", "")
    if not key and auth.lower().startswith("bearer "):
        key = auth[7:].strip()
    return key or None


def resolve(request: Request, session: Session) -> Principal | None:
    if not users_exist(session):
        if env_settings.require_auth:        # production: nobody gets in until an admin has been created
            return None
        if request.url.path.startswith("/agent") and env_settings.api_key_list:
            presented = _presented_key(request)
            if presented in env_settings.api_key_list:
                return Principal("legacy", "legacy-key", 0, frozenset({"agent:read"}))
            return None
        return Principal("anon", "anonymous", 3, frozenset(SCOPES))

    presented = _presented_key(request)
    if presented:
        if presented in env_settings.api_key_list:
            return Principal("legacy", "legacy-key", 0, frozenset({"agent:read"}))
        key = session.scalar(select(ApiKey).where(ApiKey.key_hash == sha256(presented)))
        if key is None or key.revoked_at is not None or (key.expires_at and _aware(key.expires_at) < _now()):
            return None
        key.last_used_at, key.use_count = _now(), (key.use_count or 0) + 1
        session.commit()
        scopes = frozenset(key.scopes or [])
        rank = 2 if "catalog:write" in scopes else 1 if "catalog:read" in scopes else 0
        return Principal("key", f"key:{key.name}", rank, scopes, list(key.allowed_domains or []) or None, key=key)

    token = request.cookies.get(COOKIE)
    if token:
        sess = session.scalar(select(UserSession).where(UserSession.token_hash == sha256(token)))
        if sess and _aware(sess.expires_at) > _now() and sess.user.is_active:
            u = sess.user
            return Principal("user", u.email, RANK[u.role], frozenset(SCOPES), None, user=u)
    return None


def get_principal(request: Request, session: Session = Depends(get_session)) -> Principal:
    p = resolve(request, session)
    if p is None:
        raise HTTPException(401, "Authentication required")
    request.state.actor = p.label
    request.state.principal = p
    return p


def catalog_access(request: Request, p: Principal = Depends(get_principal)) -> Principal:
    need = 1 if request.method in ("GET", "HEAD", "OPTIONS") else 2
    if p.rank < need:
        raise HTTPException(403, "Your access is read-only" if p.rank else "This credential cannot use the catalog API")
    return p


def require_admin(p: Principal = Depends(get_principal)) -> Principal:
    if p.kind not in ("user", "anon") or p.rank < RANK["admin"]:
        raise HTTPException(403, "Administrator access required")
    return p


def agent_access(p: Principal = Depends(get_principal)) -> Principal:
    if p.kind in ("key", "legacy") and "agent:read" not in p.scopes:
        raise HTTPException(403, "This API key is not allowed to read agent endpoints")
    return p


def actor_of(request: Request) -> str:
    return getattr(request.state, "actor", "steward")


# --------------------------------------------------------------------------- login routes
router = APIRouter(prefix="/api/auth", tags=["auth"])


def _cookie_secure(request: Request) -> bool:
    """`auto` marks the cookie Secure whenever the request arrived over HTTPS (also behind a TLS proxy)."""
    mode = env_settings.cookie_secure
    return mode == "always" or (mode == "auto" and request.url.scheme == "https")


def _failures_since(session: Session, email: str) -> int:
    cutoff = _now() - timedelta(seconds=env_settings.login_window_seconds)
    return session.scalar(select(func.count()).select_from(LoginAttempt)
                          .where(LoginAttempt.email == email, LoginAttempt.at > cutoff)) or 0


class Credentials(BaseModel):
    email: str = Field(min_length=3, max_length=200)
    password: str = Field(min_length=1, max_length=200)


class Setup(Credentials):
    name: str = ""
    password: str = Field(min_length=MIN_PASSWORD, max_length=200)


class PasswordChange(BaseModel):
    current: str
    new: str = Field(min_length=MIN_PASSWORD, max_length=200)


def user_out(u: User) -> dict:
    return {"id": u.id, "email": u.email, "name": u.name, "role": u.role, "is_active": u.is_active,
            "must_change_password": u.must_change_password, "created_at": u.created_at,
            "last_login_at": u.last_login_at}


def purge_expired(session: Session) -> None:
    """Housekeeping: drop expired sessions and stale failed-login records."""
    session.execute(delete(UserSession).where(UserSession.expires_at < _now()))
    session.execute(delete(LoginAttempt).where(
        LoginAttempt.at < _now() - timedelta(seconds=env_settings.login_window_seconds)))
    session.commit()


def _login(session: Session, request: Request, response: Response, user: User) -> None:
    purge_expired(session)
    token = secrets.token_urlsafe(32)
    hours = float(get_settings(session)["session_hours"] or 12)
    session.add(UserSession(token_hash=sha256(token), user_id=user.id, expires_at=_now() + timedelta(hours=hours)))
    user.last_login_at = _now()
    session.commit()
    response.set_cookie(COOKIE, token, httponly=True, samesite="lax", secure=_cookie_secure(request),
                        max_age=int(hours * 3600), path="/")


@router.get("/me")
def me(request: Request, session: Session = Depends(get_session)):
    exist = users_exist(session)
    required = exist or env_settings.require_auth
    p = resolve(request, session) if required else None
    return {
        "auth_required": required,
        "setup_needed": not exist and not env_settings.require_auth,       # open mode: UI offers "secure this catalog"
        "needs_cli_setup": not exist and env_settings.require_auth,        # production: admin is created from the CLI
        "user": user_out(p.user) if p and p.user else None,
        "org_name": get_settings(session)["org_name"],
    }


@router.post("/setup")
def setup(body: Setup, request: Request, response: Response, session: Session = Depends(get_session)):
    """Create the first administrator from the browser. Only in open mode while no users exist."""
    if env_settings.require_auth:
        raise HTTPException(403, "Browser setup is disabled. Create the first administrator with: "
                                 "python -m app.cli create-admin --email you@example.com")
    if users_exist(session):
        raise HTTPException(409, "Setup is already done")
    user = User(email=body.email.strip().lower(), name=body.name.strip(), role="admin",
                password_hash=hash_password(body.password))
    session.add(user)
    session.commit()
    _login(session, request, response, user)
    return user_out(user)


@router.post("/login")
def login(body: Credentials, request: Request, response: Response, session: Session = Depends(get_session)):
    email = body.email.strip().lower()
    if _failures_since(session, email) >= env_settings.login_max_failures:
        raise HTTPException(429, "Too many failed attempts. Try again in a few minutes.")
    user = session.scalar(select(User).where(User.email == email))
    if user is None or not user.is_active or not verify_password(body.password, user.password_hash):
        session.add(LoginAttempt(email=email[:200]))
        session.commit()
        raise HTTPException(401, "Wrong email or password")
    session.execute(delete(LoginAttempt).where(LoginAttempt.email == email))
    _login(session, request, response, user)
    return user_out(user)


@router.post("/logout")
def logout(request: Request, response: Response, session: Session = Depends(get_session)):
    token = request.cookies.get(COOKIE)
    if token:
        sess = session.scalar(select(UserSession).where(UserSession.token_hash == sha256(token)))
        if sess:
            session.delete(sess)
            session.commit()
    response.delete_cookie(COOKIE, path="/", secure=_cookie_secure(request), httponly=True, samesite="lax")
    return {"ok": True}


@router.post("/change-password")
def change_password(body: PasswordChange, p: Principal = Depends(get_principal),
                    session: Session = Depends(get_session)):
    if p.user is None:
        raise HTTPException(400, "Only signed-in people have a password")
    user = session.get(User, p.user.id)
    if not verify_password(body.current, user.password_hash):
        raise HTTPException(400, "Current password is wrong")
    user.password_hash, user.must_change_password = hash_password(body.new), False
    session.commit()
    return {"ok": True}
