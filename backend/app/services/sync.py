from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.connectors.base import TableMeta
from app.models import Column, SchemaMeta, Source, Table
from app.services.sensitive import parse_keywords, sensitive_match
from app.services.settings_store import get_settings


def load_source(session: Session, source_id: int) -> Source | None:
    """Load a source with tables+columns eagerly: sync touches all of them (500+ tables)."""
    return session.scalar(
        select(Source).where(Source.id == source_id)
        .options(selectinload(Source.tables).selectinload(Table.columns))
    )


def apply_sync(session: Session, source: Source, discovered: list[TableMeta],
               scope: list[str] | None = None) -> dict:
    """Upsert technical metadata. Never touches steward-owned semantic fields.

    `scope` is the list of schemas that were scanned; tables outside it are left alone, so syncing
    one schema never marks the rest of the lake as removed. Changed/new/removed items are flagged
    `needs_review`.
    """
    stats = {"tables_added": 0, "tables_removed": 0, "columns_added": 0, "columns_removed": 0,
             "columns_changed": 0, "columns_quarantined": 0}
    keywords = parse_keywords(get_settings(session)["pii_name_patterns"])
    existing = {(t.schema_name, t.name): t for t in source.tables}
    seen: set[tuple[str, str]] = set()

    known_schemas = {s.name for s in session.scalars(select(SchemaMeta).where(SchemaMeta.source_id == source.id))}
    for name in {m.schema_name for m in discovered} - known_schemas:
        session.add(SchemaMeta(source_id=source.id, name=name))

    for meta in discovered:
        key = (meta.schema_name, meta.name)
        seen.add(key)
        table = existing.get(key)
        if table is None:
            table = Table(source=source, schema_name=meta.schema_name, name=meta.name, needs_review=True)
            session.add(table)
            stats["tables_added"] += 1
        table.removed = False
        table.table_format = meta.table_format
        table.location = meta.location
        table.partitioned_by = meta.partitioned_by
        table.row_count = meta.row_count

        cols = {c.name: c for c in table.columns}
        seen_cols: set[str] = set()
        for cm in meta.columns:
            seen_cols.add(cm.name)
            col = cols.get(cm.name)
            if col is None:
                # Hidden from agents until a steward looks at it: it is new on a table people already know, or
                # its name looks like personal/secret data (even on a brand-new table).
                hit = sensitive_match(cm.name, keywords)
                reasons = (["New column"] if key in existing else []) + ([f"name looks sensitive ({hit})"] if hit else [])
                table.columns.append(Column(name=cm.name, data_type=cm.data_type, nullable=cm.nullable,
                                            ordinal=cm.ordinal, needs_review=True, quarantined=bool(reasons),
                                            quarantine_reason="; ".join(reasons)[:200] or None))
                stats["columns_added"] += 1
                stats["columns_quarantined"] += bool(reasons)
                if key in existing:
                    table.needs_review = True
                continue
            if col.data_type != cm.data_type:
                col.needs_review = table.needs_review = True
                stats["columns_changed"] += 1
            col.data_type, col.nullable, col.ordinal, col.removed = cm.data_type, cm.nullable, cm.ordinal, False
        for name, col in cols.items():
            if name not in seen_cols and not col.removed:
                col.removed = col.needs_review = table.needs_review = True
                stats["columns_removed"] += 1

    for key, table in existing.items():
        in_scope = scope is None or key[0] in scope
        if in_scope and key not in seen and not table.removed:
            table.removed = table.needs_review = True
            stats["tables_removed"] += 1

    source.last_synced_at = datetime.now(timezone.utc)
    session.commit()
    return stats


def table_completeness(table: Table, lang: str = "en") -> float:
    """Fraction of documentable items filled: live columns' descriptions + description/grain/type."""
    suffix = "_ar" if lang == "ar" else ""
    cols = [c for c in table.columns if not c.removed]
    documented = sum(1 for c in cols if getattr(c, "description" + suffix))
    parts = [bool(getattr(table, "description" + suffix)), bool(getattr(table, "grain" + suffix))]
    if lang != "ar":
        parts.append(bool(table.table_type))
    total = len(cols) + len(parts)
    return round((documented + sum(parts)) / total, 3) if total else 0.0


completeness = table_completeness  # kept for existing callers
