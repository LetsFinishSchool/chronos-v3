"""JSON-Logzeilen auf stdout mit ts, level, msg, correlation_id (und event_id im Worker)."""
import contextvars
import json
import logging
import sys
from datetime import UTC, datetime

correlation_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar("correlation_id", default=None)
event_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar("event_id", default=None)


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        line = {
            "ts": datetime.fromtimestamp(record.created, UTC).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
            "level": record.levelname.lower(),
            "msg": record.getMessage(),
            "correlation_id": getattr(record, "correlation_id", None) or correlation_id_var.get(),
        }
        event_id = getattr(record, "event_id", None) or event_id_var.get()
        if event_id:
            line["event_id"] = event_id
        for k, v in getattr(record, "extra_fields", {}).items():
            line[k] = v
        if record.exc_info:
            line["exc"] = self.formatException(record.exc_info)
        return json.dumps(line, ensure_ascii=False)


def setup() -> None:
    h = logging.StreamHandler(sys.stdout)
    h.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers[:] = [h]
    root.setLevel(logging.INFO)
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        lg = logging.getLogger(name)
        lg.handlers[:] = []
        lg.propagate = True
    logging.getLogger("httpx").setLevel(logging.WARNING)


log = logging.getLogger("chronos")
