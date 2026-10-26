"""Publishing rules configured by admins."""

from sqlalchemy.orm import Session

from app.models import Table
from app.services.settings_store import get_settings
from app.services.sync import completeness


def publish_blockers(session: Session, table: Table, settings: dict | None = None) -> list[str]:
    """Reasons this table may not be published right now (empty list = fine)."""
    s = settings or get_settings(session)
    problems = []
    if s["require_review_before_publish"] and table.status not in ("reviewed", "published"):
        problems.append("it must be marked reviewed first")
    need = float(s["min_completeness_to_publish"] or 0)
    if need and completeness(table) < need:
        problems.append(f"it is {round(completeness(table) * 100)}% documented but {round(need * 100)}% is required")
    return problems


def revision_blockers(session: Session, table: Table, state: dict, settings: dict | None = None) -> list[str]:
    """Reasons a pending revision may not go live, judged on the content it would produce."""
    s = settings or get_settings(session)
    need = float(s["min_completeness_to_publish"] or 0)
    if not need:
        return []
    live_cols = [c.name for c in table.columns if not c.removed]
    t = state["table"]
    documented = sum(1 for n in live_cols if state["columns"].get(n, {}).get("description"))
    parts = [bool(t.get("description")), bool(t.get("grain")), bool(t.get("table_type"))]
    got = (documented + sum(parts)) / (len(live_cols) + 3)
    if got < need:
        return [f"the result would be {round(got * 100)}% documented but {round(need * 100)}% is required"]
    return []
