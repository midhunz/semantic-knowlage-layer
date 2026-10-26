"""Defense-in-depth for the one tool that runs caller-supplied SQL (the MCP `run_query` tool).

Even though the Trino user configured for a source is expected to be read-only at the grant level,
this module never trusts that alone: only a single plain SELECT (or WITH ... SELECT) statement is
accepted, multiple statements and DDL/DML keywords are rejected outright, and the caller's query is
always wrapped in a row-capped outer SELECT regardless of what it does on its own.
"""

import re

_COMMENT = re.compile(r"--[^\n]*|/\*.*?\*/", re.DOTALL)
_FORBIDDEN = re.compile(
    r"\b(INSERT|UPDATE|DELETE|MERGE|UPSERT|CREATE|ALTER|DROP|TRUNCATE|GRANT|REVOKE|CALL|COPY|"
    r"VACUUM|EXECUTE|PREPARE|DEALLOCATE|REFRESH|UNLOAD|START\s+TRANSACTION|COMMIT|ROLLBACK)\b",
    re.IGNORECASE,
)
MAX_ROWS_CEILING = 1000
DEFAULT_ROWS = 200


def strip_comments(sql: str) -> str:
    return _COMMENT.sub(" ", sql)


def check(sql: str) -> str:
    """Raise ValueError unless `sql` is a single, plain read statement. Returns it with comments stripped."""
    if not sql or not sql.strip():
        raise ValueError("Empty query")
    body = strip_comments(sql).strip().rstrip(";").rstrip()
    if not body:
        raise ValueError("Query has no content once comments are removed")
    if ";" in body:
        raise ValueError("Only one statement is allowed")
    head = body[:10].lstrip().upper()
    if not (head.startswith("SELECT") or head.startswith("WITH")):
        raise ValueError("Only SELECT (or WITH ... SELECT) statements are allowed")
    if _FORBIDDEN.search(body):
        raise ValueError("Query contains a disallowed keyword — only read-only SELECT is permitted")
    return body


def wrap_limited(sql: str, max_rows: int) -> tuple[str, int]:
    """Always row-caps the result, regardless of what the caller's own query does."""
    n = max(1, min(int(max_rows or DEFAULT_ROWS), MAX_ROWS_CEILING))
    return f"SELECT * FROM ({sql}) AS _guarded_rows_ LIMIT {n}", n
