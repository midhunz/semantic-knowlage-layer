"""MCP server exposing the published semantic layer to agents.

Run: python -m app.mcp_server   (stdio transport)
"""

import functools

from mcp.server.fastmcp import FastMCP
from sqlalchemy import select

from app.catalog import table_rows
from app.connectors import get_connector
from app.db import SessionLocal
from app.main import _published_table_by_fqn, search_catalog
from app.models import Metric, Relationship, SampleQuery, Source, Table
from app.services import dimensions as dim_svc
from app.services import export
from app.services.settings_store import get_settings

mcp = FastMCP("semantic-layer")

# Tools that reach past the published catalog. Shown with a warning in Settings -> MCP connector.
RAW_DATA_TOOLS = {"run_query"}


def _check_allowed(name: str) -> dict:
    """Refuse the call if an administrator turned MCP, or this tool, off in Settings. Read per call, so it takes effect at once."""
    with SessionLocal() as s:
        cfg = get_settings(s)
    if not cfg["mcp_enabled"]:
        raise ValueError("MCP access is turned off by an administrator (Settings -> MCP connector).")
    if name in cfg["mcp_disabled_tools"]:
        raise ValueError(f"The tool '{name}' is turned off by an administrator (Settings -> MCP connector).")
    return cfg


def tool(fn):
    """Register an MCP tool that honours the admin settings. Name, signature and docstring are kept for clients."""
    @functools.wraps(fn)
    def guarded(*args, **kwargs):
        _check_allowed(fn.__name__)
        return fn(*args, **kwargs)
    return mcp.tool()(guarded)


@tool
def list_tables() -> list[dict]:
    """List every published table: its full name (source.schema.table), type, domain, and how
    complete its documentation is. Use this first to see what's in the catalog before searching."""
    with SessionLocal() as s:
        rows = table_rows(s, {"status": "published"})
        return [{"full_name": r["full_name"], "display_name": r["display_name"], "type": r["type"],
                 "domain": r["domain"], "certified": r["certified"], "has_description": r["has_description"],
                 "has_grain": r["has_grain"], "columns": r["columns"], "columns_documented": r["columns_documented"]}
                for r in rows]


@tool
def search_catalog_tool(query: str, lang: str | None = None) -> list[dict]:
    """Search published tables, columns (incl. synonyms) and metrics, in English or Arabic.

    lang: "en", "ar" (Arabic with English fallback) or "both"; defaults to the admin-configured language."""
    with SessionLocal() as s:
        return search_catalog(s, query, lang=lang)


@tool
def describe_table(table: str, lang: str | None = None, max_tokens: int | None = None) -> str:
    """Full LLM-ready description of a table (source.schema.table): grain, columns, joins, metrics.

    lang: "en", "ar" (Arabic with English fallback) or "both"."""
    with SessionLocal() as s:
        cfg = get_settings(s)
        doc = export.table_context(s, _published_table_by_fqn(s, table), lang or cfg["default_lang"], cfg)
        return export.render([doc], "yaml", max_tokens or cfg["default_max_tokens"] or None)


@tool
def get_join_path(tables: list[str]) -> list[dict]:
    """Return known relationships connecting any of the given tables (source.schema.table)."""
    with SessionLocal() as s:
        ids = {_published_table_by_fqn(s, t).id for t in tables}
        out = []
        for r in s.scalars(select(Relationship)):
            hidden = any(x.removed or x.quarantined for x in (r.from_column, r.to_column))
            if not hidden and r.from_column.table_id in ids and r.to_column.table_id in ids:
                out.append({"join": f"{r.from_column.table.full_name}.{r.from_column.name} = "
                                    f"{r.to_column.table.full_name}.{r.to_column.name}",
                            "cardinality": r.cardinality, "join_type": r.join_type})
        return out


@tool
def list_metrics() -> list[dict]:
    """List published business metrics with their SQL definitions."""
    with SessionLocal() as s:
        return [{"name": m.name, "description": m.description, "sql": m.sql_expression, "filters": m.filters}
                for m in s.scalars(select(Metric).where(Metric.status == "published"))]


@tool
def resolve_term(term: str) -> list[dict]:
    """Look up a business term or synonym in the glossary (English or Arabic)."""
    with SessionLocal() as s:
        return [{"term": t.term, "term_ar": t.term_ar, "definition": t.definition,
                 "definition_ar": t.definition_ar, "links": t.links}
                for t in export.glossary_resolve(s, term)]


@tool
def list_dimensions(lang: str | None = None) -> list[dict]:
    """Business dimensions answers can be broken down by (e.g. person_category), with how many values each has."""
    with SessionLocal() as s:
        cfg = get_settings(s)
        return [dim_svc.dimension_summary(d, lang or cfg["default_lang"]) for d in dim_svc.visible_dimensions(s, None)]


@tool
def describe_dimension(key: str, lang: str | None = None) -> dict:
    """Everything about one dimension: meaning, every value with its labels and aliases, families, who it
    applies to (an explicit instruction), and the columns that hold it."""
    with SessionLocal() as s:
        d = next((x for x in dim_svc.visible_dimensions(s, None) if x.key == key), None)
        if d is None:
            raise ValueError(f"No published dimension {key}")
        return dim_svc.dimension_doc(s, d, lang or get_settings(s)["default_lang"])


@tool
def resolve_value(text: str, dimension: str | None = None, lang: str | None = None) -> dict:
    """Map a word someone used ("citizens", "residents", "مقيمين") to the value stored in the data.

    Returns matches [{dimension, value, label, via}] and whether the word is ambiguous. Also reports when the
    word names a dimension itself. Use the stored `value` in queries."""
    with SessionLocal() as s:
        cfg = get_settings(s)
        return dim_svc.resolve(dim_svc.visible_dimensions(s, None), text, dimension, lang or cfg["default_lang"])


@tool
def run_query(sql: str, max_rows: int = 200) -> dict:
    """Execute a read-only SQL SELECT against the data lake and return the rows.

    Only one plain SELECT (or WITH ... SELECT) statement is accepted — no inserts/updates/DDL and no
    multiple statements; anything else is rejected before it reaches the lake. Write table names as
    schema.table (e.g. demographics.fct_population), not source.schema.table — the source prefix used
    elsewhere in this catalog (e.g. by describe_table) is this app's own addressing, not Trino's.
    Results are capped at max_rows (<=1000). This bypasses the catalog's PII and publish flags: it can
    read any column the lake's configured user can see, not just ones marked published here — use it
    deliberately. Use list_tables/describe_table for real names and resolve_value to map a word to the
    value actually stored before filtering on it."""
    with SessionLocal() as s:
        max_rows = max(1, min(max_rows, get_settings(s)["mcp_run_query_max_rows"]))
        src = s.scalar(select(Source).order_by(Source.id).limit(1))
        if src is None:
            raise ValueError("No data source is configured")
        conn = get_connector(src.kind, src.config)
        return conn.run_query(sql, max_rows)


@tool
def get_sample_queries() -> list[dict]:
    """Verified question→SQL examples to use as few-shot guidance."""
    with SessionLocal() as s:
        return [{"question": q.question, "sql": q.sql}
                for q in s.scalars(select(SampleQuery).where(SampleQuery.verified.is_(True)))]


if __name__ == "__main__":
    mcp.run()
