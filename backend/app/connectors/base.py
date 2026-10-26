from dataclasses import dataclass, field
from typing import Protocol


@dataclass
class ColumnMeta:
    name: str
    data_type: str
    nullable: bool = True
    ordinal: int = 0


@dataclass
class TableMeta:
    schema_name: str
    name: str
    columns: list[ColumnMeta] = field(default_factory=list)
    table_format: str | None = None
    location: str | None = None
    partitioned_by: list[str] = field(default_factory=list)
    row_count: int | None = None


class Connector(Protocol):
    """Reads technical metadata from a lake. Implementations must be read-only."""

    def ping(self) -> str:
        """Cheap round-trip proving credentials work; returns a short description."""
        ...

    def introspect(self, schemas: list[str] | None = None) -> list[TableMeta]: ...

    def distinct_values(self, schema: str, table: str, column: str, limit: int = 200,
                        sample_rows: int = 1_000_000) -> dict:
        """The most frequent non-null values of a column: {"values": [(value, count)], "truncated": bool}."""
        ...

    def profile_column(self, schema: str, table: str, column: str, sample_rows: int = 100_000) -> dict:
        """Return {null_fraction, distinct_count, min_value, max_value, top_values}."""
        ...

    def run_query(self, sql: str, max_rows: int = 200) -> dict:
        """Execute one caller-supplied read-only SELECT, row-capped. See app.services.sql_guard for the
        safety checks applied before this runs. Returns {columns, rows, row_count, truncated}."""
        ...
