"""Catalog data model.

Technical fields are owned by the sync job; semantic fields are owned by stewards and are
never overwritten by sync.
"""

from datetime import datetime, timezone

from sqlalchemy import (JSON, Boolean, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint, false,
                        text)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Source(Base):
    __tablename__ = "source"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), unique=True)
    kind: Mapped[str] = mapped_column(String(50), default="trino")
    # Non-secret connection settings (host, port, catalog, user). Secrets come from env vars.
    config: Mapped[dict] = mapped_column(JSON, default=dict)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    tables: Mapped[list["Table"]] = relationship(back_populates="source", cascade="all, delete-orphan")


class SchemaMeta(Base):
    """Curated description of a lake schema (a namespace of tables)."""

    __tablename__ = "schema_meta"
    __table_args__ = (UniqueConstraint("source_id", "name"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("source.id"))
    name: Mapped[str] = mapped_column(String(200))
    display_name: Mapped[str | None] = mapped_column(String(200))
    display_name_ar: Mapped[str | None] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)
    description_ar: Mapped[str | None] = mapped_column(Text)
    domain: Mapped[str | None] = mapped_column(String(100))
    owner: Mapped[str | None] = mapped_column(String(200))


class Table(Base):
    __tablename__ = "table"
    __table_args__ = (UniqueConstraint("source_id", "schema_name", "name"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("source.id"))
    schema_name: Mapped[str] = mapped_column(String(200))
    name: Mapped[str] = mapped_column(String(200))

    # --- technical (sync-owned) ---
    table_format: Mapped[str | None] = mapped_column(String(50))
    location: Mapped[str | None] = mapped_column(String(1000))
    partitioned_by: Mapped[list] = mapped_column(JSON, default=list)
    row_count: Mapped[int | None] = mapped_column(Integer)
    removed: Mapped[bool] = mapped_column(Boolean, default=False)  # dropped from lake
    needs_review: Mapped[bool] = mapped_column(Boolean, default=False)  # drift detected

    # --- semantic (steward-owned) ---
    display_name: Mapped[str | None] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)
    grain: Mapped[str | None] = mapped_column(Text)  # "one row per order line"
    table_type: Mapped[str | None] = mapped_column(String(30))  # fact|dimension|bridge|staging|aggregate
    domain: Mapped[str | None] = mapped_column(String(100))
    owner: Mapped[str | None] = mapped_column(String(200))
    refresh_cadence: Mapped[str | None] = mapped_column(String(100))
    usage_notes: Mapped[str | None] = mapped_column(Text)
    caveats: Mapped[str | None] = mapped_column(Text)
    display_name_ar: Mapped[str | None] = mapped_column(String(200))
    description_ar: Mapped[str | None] = mapped_column(Text)
    grain_ar: Mapped[str | None] = mapped_column(Text)
    usage_notes_ar: Mapped[str | None] = mapped_column(Text)
    caveats_ar: Mapped[str | None] = mapped_column(Text)
    pii_level: Mapped[str | None] = mapped_column(String(30))  # none|low|high
    certified: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String(20), default="draft")  # draft|reviewed|published
    version: Mapped[int] = mapped_column(Integer, default=0, server_default="0")  # latest published revision

    source: Mapped[Source] = relationship(back_populates="tables")
    revisions: Mapped[list["TableRevision"]] = relationship(back_populates="table", cascade="all, delete-orphan")
    columns: Mapped[list["Column"]] = relationship(
        back_populates="table", cascade="all, delete-orphan", order_by="Column.ordinal"
    )

    @property
    def fqn(self) -> str:
        return f"{self.schema_name}.{self.name}"

    @property
    def full_name(self) -> str:
        """Source-qualified name; unique across sources, used by agents."""
        return f"{self.source.name}.{self.schema_name}.{self.name}"


class Column(Base):
    __tablename__ = "column"
    __table_args__ = (UniqueConstraint("table_id", "name"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    table_id: Mapped[int] = mapped_column(ForeignKey("table.id"))
    name: Mapped[str] = mapped_column(String(200))

    # --- technical ---
    data_type: Mapped[str] = mapped_column(String(100))
    nullable: Mapped[bool] = mapped_column(Boolean, default=True)
    ordinal: Mapped[int] = mapped_column(Integer, default=0)
    removed: Mapped[bool] = mapped_column(Boolean, default=False)
    needs_review: Mapped[bool] = mapped_column(Boolean, default=False)
    # Hidden from agents until a steward reviews it (new column on a known table, or a sensitive-looking name).
    quarantined: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false())
    quarantine_reason: Mapped[str | None] = mapped_column(String(200))

    # --- semantic ---
    display_name: Mapped[str | None] = mapped_column(String(200))
    display_name_ar: Mapped[str | None] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)
    description_ar: Mapped[str | None] = mapped_column(Text)
    role: Mapped[str | None] = mapped_column(String(30))  # identifier|dimension|measure|time|attribute
    semantic_type: Mapped[str | None] = mapped_column(String(50))  # currency, percentage, email...
    unit: Mapped[str | None] = mapped_column(String(50))
    default_aggregation: Mapped[str | None] = mapped_column(String(20))  # sum|avg|min|max|count|none
    non_additive: Mapped[bool] = mapped_column(Boolean, default=False)
    allowed_values: Mapped[dict] = mapped_column(JSON, default=dict)  # code -> meaning
    example_values: Mapped[list] = mapped_column(JSON, default=list)
    format: Mapped[str | None] = mapped_column(String(100))
    synonyms: Mapped[list] = mapped_column(JSON, default=list)
    synonyms_ar: Mapped[list] = mapped_column(JSON, default=list)
    allowed_values_ar: Mapped[dict] = mapped_column(JSON, default=dict)  # code -> Arabic meaning
    is_primary_key: Mapped[bool] = mapped_column(Boolean, default=False)
    pii: Mapped[bool] = mapped_column(Boolean, default=False)
    deprecated: Mapped[bool] = mapped_column(Boolean, default=False)

    table: Mapped[Table] = relationship(back_populates="columns")


class Relationship(Base):
    __tablename__ = "relationship"

    id: Mapped[int] = mapped_column(primary_key=True)
    from_column_id: Mapped[int] = mapped_column(ForeignKey("column.id"))
    to_column_id: Mapped[int] = mapped_column(ForeignKey("column.id"))
    cardinality: Mapped[str] = mapped_column(String(20), default="many_to_one")
    join_type: Mapped[str] = mapped_column(String(20), default="left")
    description: Mapped[str | None] = mapped_column(Text)

    from_column: Mapped[Column] = relationship(foreign_keys=[from_column_id])
    to_column: Mapped[Column] = relationship(foreign_keys=[to_column_id])


class Metric(Base):
    __tablename__ = "metric"
    __table_args__ = (Index("uq_metric_name_live", "name", unique=True,
                            postgresql_where=text("draft_of_id IS NULL"), sqlite_where=text("draft_of_id IS NULL")),)

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    name_ar: Mapped[str | None] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)
    description_ar: Mapped[str | None] = mapped_column(Text)
    sql_expression: Mapped[str] = mapped_column(Text)  # e.g. SUM(net_amount)
    base_table_id: Mapped[int | None] = mapped_column(ForeignKey("table.id"))
    filters: Mapped[str | None] = mapped_column(Text)
    allowed_dimensions: Mapped[list] = mapped_column(JSON, default=list)
    synonyms: Mapped[list] = mapped_column(JSON, default=list)
    synonyms_ar: Mapped[list] = mapped_column(JSON, default=list)
    owner: Mapped[str | None] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(20), default="draft")      # draft | review | published
    # review flow: a copy (draft_of_id set) holds edits to a published item until a reviewer approves them
    draft_of_id: Mapped[int | None] = mapped_column(Integer)
    review_note: Mapped[str | None] = mapped_column(Text)            # why the last review was rejected
    submitted_by: Mapped[str | None] = mapped_column(String(200))
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class GlossaryTerm(Base):
    __tablename__ = "glossary_term"
    __table_args__ = (Index("uq_glossary_term_live", "term", unique=True,
                            postgresql_where=text("draft_of_id IS NULL"), sqlite_where=text("draft_of_id IS NULL")),)

    id: Mapped[int] = mapped_column(primary_key=True)
    term: Mapped[str] = mapped_column(String(200))
    term_ar: Mapped[str | None] = mapped_column(String(200))
    definition: Mapped[str] = mapped_column(Text)
    definition_ar: Mapped[str | None] = mapped_column(Text)
    synonyms: Mapped[list] = mapped_column(JSON, default=list)
    synonyms_ar: Mapped[list] = mapped_column(JSON, default=list)
    # Links as strings: "table:schema.name", "column:schema.name.col", "metric:name"
    links: Mapped[list] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(20), default="draft")      # draft | review | published
    # review flow: a copy (draft_of_id set) holds edits to a published item until a reviewer approves them
    draft_of_id: Mapped[int | None] = mapped_column(Integer)
    review_note: Mapped[str | None] = mapped_column(Text)            # why the last review was rejected
    submitted_by: Mapped[str | None] = mapped_column(String(200))
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class SampleQuery(Base):
    __tablename__ = "sample_query"

    id: Mapped[int] = mapped_column(primary_key=True)
    question: Mapped[str] = mapped_column(Text)
    sql: Mapped[str] = mapped_column(Text)
    tables: Mapped[list] = mapped_column(JSON, default=list)
    verified: Mapped[bool] = mapped_column(Boolean, default=False)


class Profile(Base):
    __tablename__ = "profile"

    id: Mapped[int] = mapped_column(primary_key=True)
    column_id: Mapped[int] = mapped_column(ForeignKey("column.id"), unique=True)
    null_fraction: Mapped[float | None]
    distinct_count: Mapped[int | None] = mapped_column(Integer)
    min_value: Mapped[str | None] = mapped_column(String(500))
    max_value: Mapped[str | None] = mapped_column(String(500))
    top_values: Mapped[list] = mapped_column(JSON, default=list)
    profiled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(primary_key=True)
    entity: Mapped[str] = mapped_column(String(50))
    entity_id: Mapped[int] = mapped_column(Integer)
    field: Mapped[str] = mapped_column(String(100))
    old_value: Mapped[str | None] = mapped_column(Text)
    new_value: Mapped[str | None] = mapped_column(Text)
    actor: Mapped[str] = mapped_column(String(200), default="system")
    at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    staged: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false())  # edit went to a pending revision


class TableRevision(Base):
    """A version of a published table's semantic content.

    status "pending": the single working copy (`changes` = new values, not yet live).
    status "published": an immutable version (`snapshot` = full semantic state after it, `diff` = what it changed).
    """

    __tablename__ = "table_revision"
    __table_args__ = (
        UniqueConstraint("table_id", "number"),
        Index("uq_table_revision_one_pending", "table_id", unique=True,
              postgresql_where=text("status = 'pending'"), sqlite_where=text("status = 'pending'")),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    table_id: Mapped[int] = mapped_column(ForeignKey("table.id"))
    number: Mapped[int | None] = mapped_column(Integer)  # assigned when published
    status: Mapped[str] = mapped_column(String(20), default="pending")
    changes: Mapped[dict] = mapped_column(JSON, default=dict)      # {"table": {f: v}, "columns": {name: {f: v}}}
    diff: Mapped[list] = mapped_column(JSON, default=list)         # [{scope, column, field, old, new}] at publish
    snapshot: Mapped[dict | None] = mapped_column(JSON)
    message: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[str] = mapped_column(String(200), default="system")
    contributors: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    published_by: Mapped[str | None] = mapped_column(String(200))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    table: Mapped[Table] = relationship(back_populates="revisions")


# ------------------------------------------------------------------ access control & integrations
class User(Base):
    __tablename__ = "app_user"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(200), unique=True)
    name: Mapped[str] = mapped_column(String(200), default="")
    role: Mapped[str] = mapped_column(String(20), default="viewer")  # admin | steward | viewer
    password_hash: Mapped[str] = mapped_column(String(300))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    must_change_password: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class UserSession(Base):
    __tablename__ = "user_session"

    id: Mapped[int] = mapped_column(primary_key=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("app_user.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    user: Mapped[User] = relationship()


class ApiKey(Base):
    """A credential for one consuming application. Only a hash of the secret is stored."""

    __tablename__ = "api_key"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)
    key_prefix: Mapped[str] = mapped_column(String(24))  # shown in the UI to identify the key
    key_hash: Mapped[str] = mapped_column(String(64), unique=True)
    scopes: Mapped[list] = mapped_column(JSON, default=list)  # agent:read | catalog:read | catalog:write
    allowed_domains: Mapped[list] = mapped_column(JSON, default=list)  # empty = every domain
    created_by: Mapped[str | None] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    use_count: Mapped[int] = mapped_column(Integer, default=0)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AppSetting(Base):
    __tablename__ = "app_setting"

    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    value: Mapped[dict] = mapped_column(JSON)  # {"v": <value>} so any JSON type round-trips


class Webhook(Base):
    __tablename__ = "webhook"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    url: Mapped[str] = mapped_column(String(1000))
    secret: Mapped[str] = mapped_column(String(100))  # HMAC signing key shared with the receiver
    events: Mapped[list] = mapped_column(JSON, default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    last_delivery_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_status: Mapped[str | None] = mapped_column(String(200))


class LoginAttempt(Base):
    """Failed sign-ins, kept in the database so the throttle holds across worker processes and restarts."""

    __tablename__ = "login_attempt"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(200), index=True)
    at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, index=True)


# ------------------------------------------------------------------ dimensions (business vocabulary)
class Dimension(Base):
    """A business concept agents can break answers down by (e.g. person_category), independent of any one table."""

    __tablename__ = "dimension"
    __table_args__ = (Index("uq_dimension_key_live", "key", unique=True,
                            postgresql_where=text("draft_of_id IS NULL"), sqlite_where=text("draft_of_id IS NULL")),)

    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(String(64))       # immutable slug other rules refer to
    label: Mapped[str | None] = mapped_column(String(200))
    label_ar: Mapped[str | None] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)           # "what it means": read by the agent's planner
    description_ar: Mapped[str | None] = mapped_column(Text)
    synonyms: Mapped[list] = mapped_column(JSON, default=list)      # words that name the dimension itself
    synonyms_ar: Mapped[list] = mapped_column(JSON, default=list)
    # [{"term", "term_ar", "values": [stored values]}]: one business word standing for several values
    families: Mapped[list] = mapped_column(JSON, default=list)
    # Who the dimension applies to: [{"dimension": key, "values": [...]}], ANDed. Empty = everyone.
    applies_to: Mapped[list] = mapped_column(JSON, default=list)
    applies_note: Mapped[str | None] = mapped_column(Text)
    applies_note_ar: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="draft")  # draft | review | published (agents see published only)
    # review flow: a copy (draft_of_id set) holds edits to a published item until a reviewer approves them
    draft_of_id: Mapped[int | None] = mapped_column(Integer)
    review_note: Mapped[str | None] = mapped_column(Text)            # why the last review was rejected
    submitted_by: Mapped[str | None] = mapped_column(String(200))
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    values: Mapped[list["DimensionValue"]] = relationship(
        back_populates="dimension", cascade="all, delete-orphan", order_by="DimensionValue.position, DimensionValue.id")
    bindings: Mapped[list["DimensionBinding"]] = relationship(back_populates="dimension", cascade="all, delete-orphan")


class DimensionValue(Base):
    __tablename__ = "dimension_value"
    __table_args__ = (UniqueConstraint("dimension_id", "value"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    dimension_id: Mapped[int] = mapped_column(ForeignKey("dimension.id"))
    value: Mapped[str] = mapped_column(String(200))                 # exactly as stored in the data
    label: Mapped[str | None] = mapped_column(String(200))
    label_ar: Mapped[str | None] = mapped_column(String(200))
    aliases: Mapped[list] = mapped_column(JSON, default=list)       # words people say, either language
    position: Mapped[int] = mapped_column(Integer, default=0)

    dimension: Mapped[Dimension] = relationship(back_populates="values")


class DimensionBinding(Base):
    """A physical column that holds this dimension's values. A column belongs to at most one dimension
    (a draft copy repeats its live dimension's bindings, so that rule is checked in code, not by the database)."""

    __tablename__ = "dimension_binding"

    id: Mapped[int] = mapped_column(primary_key=True)
    dimension_id: Mapped[int] = mapped_column(ForeignKey("dimension.id"))
    column_id: Mapped[int] = mapped_column(ForeignKey("column.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    dimension: Mapped[Dimension] = relationship(back_populates="bindings")
    column: Mapped[Column] = relationship()
