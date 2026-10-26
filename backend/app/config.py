"""Runtime configuration, all from SL_* environment variables (or a .env file).

Development is the default and stays zero-config (SQLite, open until the first admin exists).
Production (SL_ENV=production) is strict: see validate_for_production().
"""

from typing import Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SL_", env_file=".env", extra="ignore")

    env: Literal["development", "production"] = "development"
    # SQLite for local development; Postgres for anything real, e.g. postgresql://user:pass@host:5432/db
    database_url: str = "sqlite:///./semantic_layer.db"
    db_pool_size: int = 10
    db_max_overflow: int = 10

    # Legacy: comma-separated agent-only keys accepted when no accounts exist (prefer API keys in Settings).
    api_keys: str = ""

    # Browser origins allowed to call the API cross-site. Empty = same-origin only (the production default).
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    # Session cookie `Secure` flag: "auto" sets it whenever the request arrived over HTTPS.
    cookie_secure: Literal["auto", "always", "never"] = "auto"
    # Refuse anonymous access even before the first admin exists. Defaults to True in production.
    require_auth: bool | None = None
    # Directory with the built web UI; when set the API also serves it (single-container deploys).
    static_dir: str = ""
    log_level: str = "INFO"
    log_json: bool = False

    # Optional: create this administrator at startup if no users exist yet (idempotent).
    bootstrap_admin_email: str = ""
    bootstrap_admin_password: str = ""

    login_max_failures: int = 5          # per email, per window
    login_window_seconds: int = 300
    allow_sqlite_in_production: bool = False
    # Interactive /docs and /openapi.json are off by default in production (they list every
    # endpoint, unauthenticated). Set true to keep them available anyway.
    enable_docs: bool = False

    @model_validator(mode="after")
    def _defaults(self):
        if self.require_auth is None:
            self.require_auth = self.env == "production"
        if self.env == "production" and "cors_origins" not in self.model_fields_set:
            self.cors_origins = ""
        return self

    @property
    def is_production(self) -> bool:
        return self.env == "production"

    @property
    def docs_enabled(self) -> bool:
        return self.enable_docs or not self.is_production

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")

    @property
    def api_key_list(self) -> list[str]:
        return [k.strip() for k in self.api_keys.split(",") if k.strip()]

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()


def validate_for_production(s: Settings = settings) -> list[str]:
    """Raise on settings that are unsafe in production; return non-fatal warnings."""
    problems, warnings = [], []
    if s.is_production:
        if s.is_sqlite and not s.allow_sqlite_in_production:
            problems.append("SL_DATABASE_URL points at SQLite. Use Postgres in production "
                            "(or set SL_ALLOW_SQLITE_IN_PRODUCTION=true for a single-node trial).")
        if s.cookie_secure == "never":
            problems.append("SL_COOKIE_SECURE=never would send session cookies over plain HTTP.")
        if not s.require_auth:
            problems.append("SL_REQUIRE_AUTH=false leaves the catalog open to anyone until an admin exists.")
        if any("localhost" in o or "127.0.0.1" in o for o in s.cors_origin_list):
            warnings.append("SL_CORS_ORIGINS allows localhost origins in production.")
        if s.api_key_list:
            warnings.append("SL_API_KEYS (legacy shared keys) is set; prefer per-application keys in Settings.")
        if s.enable_docs:
            warnings.append("SL_ENABLE_DOCS=true: /docs and /openapi.json list every endpoint and are reachable "
                            "without authentication.")
    if problems:
        raise RuntimeError("Refusing to start in production:\n  - " + "\n  - ".join(problems))
    return warnings
