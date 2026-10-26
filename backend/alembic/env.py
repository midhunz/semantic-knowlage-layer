"""Alembic environment. Uses the app's own engine/settings so `alembic` and the app always agree."""

from alembic import context

import app.models  # noqa: F401  (registers every table on Base.metadata)
from app.db import Base, engine

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(url=str(engine.url), target_metadata=target_metadata, literal_binds=True,
                      dialect_opts={"paramstyle": "named"}, render_as_batch=engine.dialect.name == "sqlite")
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    # A connection may be handed in (tests / app.migrate); otherwise open one from the app engine.
    connectable = context.config.attributes.get("connection")
    if connectable is not None:
        _run(connectable)
        return
    with engine.connect() as conn:
        _run(conn)


def _run(conn) -> None:
    context.configure(connection=conn, target_metadata=target_metadata, compare_type=True,
                      render_as_batch=conn.dialect.name == "sqlite")
    with context.begin_transaction():
        context.run_migrations()
    conn.commit()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
