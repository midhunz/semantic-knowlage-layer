"""Cross-cutting web concerns: lifespan startup, security headers, request ids, error handling, UI serving."""

import logging
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import func, select, text

from app import migrate as mig
from app.auth import hash_password, purge_expired
from app.config import settings, validate_for_production
from app.db import SessionLocal, describe_url
from app.db import engine as default_engine
from app.logging_config import setup_logging
from app.models import User

log = logging.getLogger("semantic_layer")

# The UI uses inline style attributes (React `style={}`), so style-src needs 'unsafe-inline'; scripts stay strict.
CSP = ("default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; font-src 'self'; "
       "connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'")
# FastAPI's built-in Swagger UI (SL_ENABLE_DOCS) loads its JS/CSS from jsdelivr and runs an inline
# <script>; the default CSP above blocks all of that silently, leaving an empty page. Scoped to /docs only.
DOCS_CSP = ("default-src 'self'; img-src 'self' data: https://fastapi.tiangolo.com; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "font-src 'self' https://cdn.jsdelivr.net; connect-src 'self'; "
            "frame-ancestors 'none'; base-uri 'self'; form-action 'self'")
API_PREFIXES = ("/api", "/agent", "/health", "/ready", "/docs", "/openapi.json", "/redoc")


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    for w in validate_for_production():
        log.warning(w)
    log.info("Starting in %s mode, database %s", settings.env, describe_url())
    log.info("Migrations: %s", mig.ensure_schema_current(auto=not settings.is_production))
    _bootstrap_admin()
    with SessionLocal() as s:
        purge_expired(s)
    yield


def _bootstrap_admin() -> None:
    """SL_BOOTSTRAP_ADMIN_EMAIL/PASSWORD create the first administrator when no users exist (idempotent)."""
    email, pw = settings.bootstrap_admin_email.strip().lower(), settings.bootstrap_admin_password
    if not email or not pw:
        return
    with SessionLocal() as s:
        if (s.scalar(select(func.count()).select_from(User)) or 0) > 0:
            return
        s.add(User(email=email, name="Administrator", role="admin", password_hash=hash_password(pw)))
        s.commit()
        log.warning("Created bootstrap administrator %s — remove SL_BOOTSTRAP_ADMIN_PASSWORD from the environment now", email)


def install(app: FastAPI) -> None:
    @app.middleware("http")
    async def harden(request: Request, call_next):
        rid = request.headers.get("x-request-id") or uuid.uuid4().hex[:12]
        request.state.request_id = rid
        started = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:  # never leak a stack trace to the client; log it with the request id
            log.exception("Unhandled error", extra={"request_id": rid, "method": request.method, "path": request.url.path})
            response = JSONResponse({"detail": "Internal server error", "request_id": rid}, status_code=500)
        path = request.url.path
        h = response.headers
        h["X-Request-ID"] = rid
        h["X-Content-Type-Options"] = "nosniff"
        h["X-Frame-Options"] = "DENY"
        h["Referrer-Policy"] = "same-origin"
        h["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        h["Content-Security-Policy"] = DOCS_CSP if path.startswith("/docs") else CSP
        if request.url.scheme == "https":
            h["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        if path.startswith(("/api", "/agent")):
            h["Cache-Control"] = "no-store"          # catalog data and credentials-adjacent responses
        if path.startswith("/api") or response.status_code >= 500:
            log.info("%s %s -> %s", request.method, path, response.status_code,
                     extra={"request_id": rid, "method": request.method, "path": path,
                            "status": response.status_code, "ms": round((time.perf_counter() - started) * 1000)})
        return response

    @app.get("/health", include_in_schema=False)
    def health():
        """Liveness: the process is up. Cheap, no database."""
        return {"ok": True}

    @app.get("/ready", include_in_schema=False)
    def ready():
        """Readiness: the database answers and the schema is at the version this code needs."""
        try:
            with default_engine.connect() as c:
                c.execute(text("SELECT 1"))
            rev, head = mig.current_revision(), mig.head_revision()
        except Exception as e:  # noqa: BLE001
            return JSONResponse({"ready": False, "detail": f"database unavailable: {type(e).__name__}"}, status_code=503)
        if rev != head:
            return JSONResponse({"ready": False, "detail": f"schema {rev} != {head}; run migrations"}, status_code=503)
        return {"ready": True, "schema": rev}


class _Assets(StaticFiles):
    async def get_response(self, path, scope):
        resp = await super().get_response(path, scope)
        resp.headers["Cache-Control"] = "public, max-age=31536000, immutable"   # filenames are content-hashed
        return resp


def serve_ui(app: FastAPI) -> bool:
    """Serve the built web UI (and its client-side routes) from the API when SL_STATIC_DIR is set."""
    root = Path(settings.static_dir) if settings.static_dir else None
    if not root or not (root / "index.html").exists():
        return False
    if (root / "assets").is_dir():
        app.mount("/assets", _Assets(directory=root / "assets"), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    def spa(path: str):
        if ("/" + path).startswith(API_PREFIXES):
            raise HTTPException(404, "Not found")
        target = (root / path).resolve()
        if path and target.is_file() and root.resolve() in target.parents:     # e.g. /vendor/icp-logo.png
            return FileResponse(target)
        return FileResponse(root / "index.html", headers={"Cache-Control": "no-cache"})

    return True
