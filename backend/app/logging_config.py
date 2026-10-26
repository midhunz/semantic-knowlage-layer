import json
import logging
import sys
from datetime import datetime, timezone

from app.config import settings


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        out = {"ts": datetime.now(timezone.utc).isoformat(), "level": record.levelname,
               "logger": record.name, "msg": record.getMessage()}
        for key in ("request_id", "method", "path", "status", "ms"):
            if hasattr(record, key):
                out[key] = getattr(record, key)
        if record.exc_info:
            out["exc"] = self.formatException(record.exc_info)
        return json.dumps(out, ensure_ascii=False)


def setup_logging() -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter() if settings.log_json else
                         logging.Formatter("%(asctime)s %(levelname)-7s %(name)s: %(message)s"))
    root = logging.getLogger()
    root.handlers[:] = [handler]
    root.setLevel(settings.log_level.upper())
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
