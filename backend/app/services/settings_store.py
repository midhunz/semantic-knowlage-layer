"""Admin-configurable settings, stored as key → JSON in the catalog DB."""

from sqlalchemy.orm import Session

from app.models import AppSetting
from app.services.sensitive import DEFAULT_KEYWORDS

DEFAULTS: dict = {
    "org_name": "",
    "default_lang": "en",              # language agents get when they don't ask for one: en | ar | both
    "default_max_tokens": 0,            # 0 = no trimming unless the caller asks
    "pii_columns_in_agent_output": "names_only",  # names_only | exclude
    "require_review_before_publish": False,
    "min_completeness_to_publish": 0.0,  # 0..1 share of a table's documentation that must be filled
    "session_hours": 12,
    # New columns, and columns whose name matches, are hidden from agents until a steward releases them.
    "pii_name_patterns": DEFAULT_KEYWORDS,
    # When on, whoever publishes a pending revision must not be one of the people who edited it.
    "revision_requires_different_approver": False,
    # MCP connector (stdio): master switch, tools an administrator has turned off, and a ceiling on run_query rows.
    "mcp_enabled": True,
    "mcp_disabled_tools": [],
    "mcp_run_query_max_rows": 1000,
}

CHOICES = {"default_lang": {"en", "ar", "both"}, "pii_columns_in_agent_output": {"names_only", "exclude"}}


def get_settings(session: Session) -> dict:
    out = dict(DEFAULTS)
    for row in session.query(AppSetting):
        if row.key in DEFAULTS:
            out[row.key] = row.value.get("v", DEFAULTS[row.key])
    return out


def save_settings(session: Session, values: dict) -> dict:
    for key, value in values.items():
        if key not in DEFAULTS:
            raise ValueError(f"Unknown setting {key}")
        if key in CHOICES and value not in CHOICES[key]:
            raise ValueError(f"{key} must be one of {sorted(CHOICES[key])}")
        row = session.get(AppSetting, key)
        if row is None:
            session.add(AppSetting(key=key, value={"v": value}))
        else:
            row.value = {"v": value}
    session.commit()
    return get_settings(session)
