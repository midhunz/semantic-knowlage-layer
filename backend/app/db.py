from collections.abc import Iterator

from sqlalchemy import MetaData, create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import settings


def normalize_url(url: str) -> str:
    """Accept plain `postgres://` / `postgresql://` URLs and use the psycopg 3 driver for them."""
    for prefix in ("postgres://", "postgresql://"):
        if url.startswith(prefix):
            return "postgresql+psycopg://" + url[len(prefix):]
    return url


def make_engine(url: str):
    url = normalize_url(url)
    if url.startswith("sqlite"):
        kwargs: dict = {"connect_args": {"check_same_thread": False}}
        if url in ("sqlite://", "sqlite:///:memory:"):
            kwargs["poolclass"] = StaticPool
        return create_engine(url, **kwargs)
    return create_engine(url, pool_pre_ping=True, pool_size=settings.db_pool_size,
                         max_overflow=settings.db_max_overflow, pool_recycle=1800)


engine = make_engine(settings.database_url)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

# Stable constraint names: required for reliable Alembic migrations (especially SQLite batch mode).
NAMING = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING)


def get_session() -> Iterator[Session]:
    with SessionLocal() as session:
        yield session


def describe_url(url: str | None = None) -> str:
    """Connection string safe to log (password hidden)."""
    return make_url(normalize_url(url or settings.database_url)).render_as_string(hide_password=True)


def ensure_columns(eng=None) -> None:
    """Legacy adoption only: add columns that were added to the models after a pre-Alembic DB was created."""
    from sqlalchemy import inspect, text

    eng = eng or engine
    insp = inspect(eng)
    for table in Base.metadata.sorted_tables:
        if not insp.has_table(table.name):
            continue
        existing = {c["name"] for c in insp.get_columns(table.name)}
        for col in table.columns:
            if col.name not in existing:
                ddl = col.type.compile(eng.dialect)
                with eng.begin() as conn:
                    conn.execute(text(f'ALTER TABLE "{table.name}" ADD COLUMN "{col.name}" {ddl}'))
