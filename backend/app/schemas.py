from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Status = Literal["draft", "reviewed", "published"]


class SourceIn(BaseModel):
    # no dots: names are used as the first part of source.schema.table
    name: str = Field(min_length=1, max_length=100, pattern=r"^[A-Za-z0-9][A-Za-z0-9_-]*$")
    kind: Literal["trino"] = "trino"
    config: dict


class SourceOut(SourceIn):
    model_config = ConfigDict(from_attributes=True)
    id: int


class TableUpdate(BaseModel):
    display_name: str | None = None
    display_name_ar: str | None = None
    description: str | None = None
    description_ar: str | None = None
    grain: str | None = None
    grain_ar: str | None = None
    usage_notes_ar: str | None = None
    caveats_ar: str | None = None
    table_type: Literal["fact", "dimension", "bridge", "staging", "aggregate"] | None = None
    domain: str | None = None
    owner: str | None = None
    refresh_cadence: str | None = None
    usage_notes: str | None = None
    caveats: str | None = None
    pii_level: Literal["none", "low", "high"] | None = None
    certified: bool | None = None
    status: Status | None = None
    needs_review: bool | None = None


class ColumnUpdate(BaseModel):
    display_name: str | None = None
    display_name_ar: str | None = None
    description: str | None = None
    description_ar: str | None = None
    synonyms_ar: list[str] | None = None
    allowed_values_ar: dict | None = None
    role: Literal["identifier", "dimension", "measure", "time", "attribute"] | None = None
    semantic_type: str | None = None
    unit: str | None = None
    default_aggregation: Literal["sum", "avg", "min", "max", "count", "none"] | None = None
    non_additive: bool | None = None
    allowed_values: dict | None = None
    example_values: list | None = None
    format: str | None = None
    synonyms: list[str] | None = None
    is_primary_key: bool | None = None
    pii: bool | None = None
    deprecated: bool | None = None
    needs_review: bool | None = None
    quarantined: bool | None = None


class RelationshipIn(BaseModel):
    from_column_id: int
    to_column_id: int
    cardinality: Literal["one_to_one", "many_to_one", "one_to_many", "many_to_many"] = "many_to_one"
    join_type: Literal["inner", "left"] = "left"
    description: str | None = None


class MetricIn(BaseModel):
    name: str
    name_ar: str | None = None
    description: str | None = None
    description_ar: str | None = None
    synonyms_ar: list[str] = []
    sql_expression: str
    base_table_id: int | None = None
    filters: str | None = None
    allowed_dimensions: list[str] = []
    synonyms: list[str] = []
    owner: str | None = None
    status: Status = "draft"


class GlossaryIn(BaseModel):
    term: str
    term_ar: str | None = None
    definition: str
    definition_ar: str | None = None
    synonyms_ar: list[str] = []
    synonyms: list[str] = []
    links: list[str] = []


class SampleQueryIn(BaseModel):
    question: str
    sql: str
    tables: list[str] = []
    verified: bool = False


class SchemaMetaUpdate(BaseModel):
    display_name: str | None = None
    display_name_ar: str | None = None
    description: str | None = None
    description_ar: str | None = None
    domain: str | None = None
    owner: str | None = None


class BulkTableUpdate(BaseModel):
    """Select tables by explicit ids OR by the same filters the catalog grid uses."""
    ids: list[int] | None = None
    filters: dict | None = None
    patch: TableUpdate


class ColumnGroupApply(BaseModel):
    """Apply a column definition to every column with this name (optionally scoped)."""
    name: str
    patch: ColumnUpdate
    only_empty: bool = True  # fill blank fields only; False overwrites
    source_id: int | None = None
    schema_name: str | None = None
