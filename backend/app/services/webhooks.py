"""Outbound webhooks: tell other applications when the semantic layer changes.

Each delivery is a JSON POST signed with `X-SL-Signature: sha256=<hmac of the body, keyed by the webhook secret>`.
Delivery is best-effort in a background thread; the last result is recorded on the webhook.
"""

import hashlib
import hmac
import json
import threading
import urllib.error
import urllib.request
from datetime import datetime, timezone

from sqlalchemy import select

from app.db import SessionLocal
from app.models import Webhook

EVENTS = {
    "table.published": "A table was published to agents",
    "table.unpublished": "A table was withdrawn from agents",
    "table.updated": "A new version of a published table went live",
    "dimension.updated": "A published dimension (its values, aliases or rules) changed",
    "metric.updated": "A published metric was approved or changed",
    "glossary.updated": "A published glossary term was approved or changed",
    "catalog.synced": "A source finished syncing",
    "webhook.test": "Sent when you press “Send test”",
}
TIMEOUT = 5


def sign(secret: str, body: bytes) -> str:
    return "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def deliver(url: str, secret: str, event: str, payload: dict) -> str:
    """POST one event; returns a short status string (never raises)."""
    body = json.dumps({"event": event, "sent_at": datetime.now(timezone.utc).isoformat(), "data": payload},
                      ensure_ascii=False).encode()
    req = urllib.request.Request(url, data=body, method="POST", headers={
        "Content-Type": "application/json", "User-Agent": "semantic-layer-webhook/1",
        "X-SL-Event": event, "X-SL-Signature": sign(secret, body)})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return f"{resp.status} OK"
    except urllib.error.HTTPError as e:
        return f"{e.code} {e.reason}"
    except Exception as e:  # network errors, bad URL, timeouts
        return f"failed: {type(e).__name__}: {e}"[:190]


def _run(hook_id: int, url: str, secret: str, event: str, payload: dict) -> None:
    status = deliver(url, secret, event, payload)
    with SessionLocal() as s:
        hook = s.get(Webhook, hook_id)
        if hook:
            hook.last_delivery_at, hook.last_status = datetime.now(timezone.utc), status
            s.commit()


def emit(session, event: str, payload: dict) -> int:
    """Queue `event` to every active webhook subscribed to it. Returns how many were queued."""
    hooks = session.scalars(select(Webhook).where(Webhook.is_active.is_(True))).all()
    n = 0
    for h in hooks:
        if event in (h.events or []):
            threading.Thread(target=_run, args=(h.id, h.url, h.secret, event, payload), daemon=True).start()
            n += 1
    return n
