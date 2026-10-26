"""Schema migrations (Alembic) with safe adoption of databases created before migrations existed."""

import logging
from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import inspect

from app.db import Base, ensure_columns
from app.db import engine as default_engine

log = logging.getLogger("semantic_layer.migrate")
BACKEND_DIR = Path(__file__).resolve().parent.parent


def alembic_config() -> Config:
    cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    return cfg


def head_revision() -> str:
    return ScriptDirectory.from_config(alembic_config()).get_current_head()


def current_revision(eng=None) -> str | None:
    with (eng or default_engine).connect() as conn:
        return MigrationContext.configure(conn).get_current_revision()


def is_legacy(eng=None) -> bool:
    """A database made by the old create_all() startup: has our tables but no migration history."""
    eng = eng or default_engine
    insp = inspect(eng)
    return insp.has_table("source") and current_revision(eng) is None


def upgrade(eng=None) -> None:
    eng = eng or default_engine
    cfg = alembic_config()
    with eng.connect() as conn:
        cfg.attributes["connection"] = conn
        command.upgrade(cfg, "head")


def adopt_legacy(eng=None) -> None:
    """Bring a pre-migration database up to the current models, then record it as being at head."""
    eng = eng or default_engine
    log.warning("Adopting a database created before migrations existed; stamping it at head")
    Base.metadata.create_all(eng)       # only creates tables that are missing
    ensure_columns(eng)                 # only adds columns that are missing
    cfg = alembic_config()
    with eng.connect() as conn:
        cfg.attributes["connection"] = conn
        command.stamp(cfg, "head")
        conn.commit()


def migrate(eng=None) -> str:
    """Explicit `migrate`: adopt-if-legacy, then upgrade to head. Returns a human-readable result."""
    eng = eng or default_engine
    if is_legacy(eng):
        adopt_legacy(eng)
        return f"adopted existing database at {head_revision()}"
    before = current_revision(eng)
    upgrade(eng)
    after = current_revision(eng)
    return f"already at {after}" if before == after else f"upgraded {before or 'empty'} -> {after}"


def ensure_schema_current(auto: bool, eng=None) -> str:
    """Startup check. Development (auto=True) migrates by itself; production only verifies."""
    eng = eng or default_engine
    head = head_revision()
    rev = current_revision(eng)
    if rev == head:
        return f"schema at {head}"
    if auto:
        return migrate(eng)
    if is_legacy(eng):
        raise RuntimeError("The database predates migrations. Run: python -m app.cli migrate")
    raise RuntimeError(f"The database schema is at {rev or 'nothing'} but this version needs {head}. "
                       "Run: python -m app.cli migrate")
