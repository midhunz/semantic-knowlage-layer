import os
import re

import trino

from app.connectors.base import ColumnMeta, TableMeta
from app.services import sql_guard

_IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_SYSTEM_SCHEMAS = {"information_schema", "system"}


def _ident(value: str) -> str:
    if not _IDENT.match(value):
        raise ValueError(f"Unsafe identifier: {value!r}")
    return f'"{value}"'


class TrinoConnector:
    """Introspects an Iceberg (or any) Trino catalog. Config: host, port, catalog, user, http_scheme.

    The password, if any, is read from the env var named by config["password_env"].
    """

    def __init__(self, config: dict):
        self.catalog = config["catalog"]
        auth = None
        if config.get("password_env"):
            auth = trino.auth.BasicAuthentication(config["user"], os.environ[config["password_env"]])
        self._conn = trino.dbapi.connect(
            host=config["host"],
            port=config.get("port", 8080),
            user=config["user"],
            catalog=self.catalog,
            http_scheme=config.get("http_scheme", "http"),
            auth=auth,
            request_timeout=60,
        )

    def _query(self, sql: str, params: list | None = None) -> list[tuple]:
        cur = self._conn.cursor()
        cur.execute(sql, params)
        return cur.fetchall()

    def ping(self) -> str:
        version = self._query("SELECT version()")[0][0]
        n = len({r[0] for r in self._query(
            f"SELECT schema_name FROM {_ident(self.catalog)}.information_schema.schemata")})
        return f"Trino {version} · catalog '{self.catalog}' · {n} schemas"

    def introspect(self, schemas: list[str] | None = None) -> list[TableMeta]:
        cat = _ident(self.catalog)
        rows = self._query(
            f"SELECT table_schema, table_name, column_name, data_type, is_nullable, ordinal_position "
            f"FROM {cat}.information_schema.columns "
            f"WHERE table_schema <> 'information_schema' ORDER BY 1, 2, 6"
        )
        tables: dict[tuple[str, str], TableMeta] = {}
        for schema, table, col, dtype, nullable, pos in rows:
            if schema in _SYSTEM_SCHEMAS or (schemas and schema not in schemas):
                continue
            t = tables.setdefault((schema, table), TableMeta(schema, table, table_format="iceberg"))
            t.columns.append(ColumnMeta(col, dtype, str(nullable).upper() == "YES", pos))
        for t in tables.values():
            self._enrich_iceberg(t)
        return list(tables.values())

    def _enrich_iceberg(self, t: TableMeta) -> None:
        """Best-effort: row count + location + partitioning. Failures leave fields unset."""
        fq = f"{_ident(self.catalog)}.{_ident(t.schema_name)}.{_ident(t.name)}"
        try:
            ddl = self._query(f"SHOW CREATE TABLE {fq}")[0][0]
            if m := re.search(r"location = '([^']+)'", ddl):
                t.location = m.group(1)
            if m := re.search(r"partitioning = ARRAY\[([^\]]*)\]", ddl):
                t.partitioned_by = [p.strip().strip("'") for p in m.group(1).split(",") if p.strip()]
        except Exception:
            pass
        try:
            summary_fq = f'{_ident(self.catalog)}.{_ident(t.schema_name)}."{t.name}$partitions"'
            t.row_count = self._query(f"SELECT COALESCE(SUM(record_count), 0) FROM {summary_fq}")[0][0]
        except Exception:
            pass

    def distinct_values(self, schema: str, table: str, column: str, limit: int = 200,
                        sample_rows: int = 1_000_000) -> dict:
        """Most frequent non-null values (as text) within the first `sample_rows` rows; counts are of that sample."""
        fq = f"{_ident(self.catalog)}.{_ident(schema)}.{_ident(table)}"
        c = _ident(column)
        rows = self._query(
            f"SELECT CAST(v AS VARCHAR), COUNT(*) AS n FROM (SELECT {c} AS v FROM {fq} LIMIT {int(sample_rows)}) "
            f"WHERE v IS NOT NULL GROUP BY 1 ORDER BY n DESC, 1 LIMIT {int(limit) + 1}")
        return {"values": [(str(v)[:200], int(n)) for v, n in rows[:limit]], "truncated": len(rows) > limit}

    def profile_column(self, schema: str, table: str, column: str, sample_rows: int = 100_000) -> dict:
        fq = f"{_ident(self.catalog)}.{_ident(schema)}.{_ident(table)}"
        c = _ident(column)
        sample = f"(SELECT {c} AS v FROM {fq} LIMIT {int(sample_rows)})"
        nulls, distinct, mn, mx = self._query(
            f"SELECT CAST(COUNT_IF(v IS NULL) AS DOUBLE) / NULLIF(COUNT(*), 0), "
            f"APPROX_DISTINCT(v), CAST(MIN(v) AS VARCHAR), CAST(MAX(v) AS VARCHAR) FROM {sample}"
        )[0]
        top = self._query(
            f"SELECT CAST(v AS VARCHAR), COUNT(*) AS n FROM {sample} WHERE v IS NOT NULL "
            f"GROUP BY 1 ORDER BY n DESC LIMIT 10"
        )
        return {
            "null_fraction": nulls,
            "distinct_count": distinct,
            "min_value": mn,
            "max_value": mx,
            "top_values": [{"value": v, "count": n} for v, n in top],
        }

    def run_query(self, sql: str, max_rows: int = 200) -> dict:
        """Execute one caller-supplied read-only SELECT. `sql_guard` rejects anything but a single plain
        SELECT/WITH statement up front; the result is always wrapped in a row-capped outer SELECT
        regardless of what the caller's own query does (a LIMIT inside it is redundant, not required)."""
        checked = sql_guard.check(sql)
        wrapped, cap = sql_guard.wrap_limited(checked, max_rows)
        cur = self._conn.cursor()
        cur.execute(wrapped)
        rows = cur.fetchall()
        columns = [d[0] for d in (cur.description or [])]

        def jsonable(v):
            return v if v is None or isinstance(v, (int, float, bool, str)) else str(v)[:500]

        return {
            "columns": columns,
            "rows": [[jsonable(v) for v in r] for r in rows],
            "row_count": len(rows),
            "truncated": len(rows) >= cap,
        }
