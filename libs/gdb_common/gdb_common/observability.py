"""
Shared observability for GDB services (Enterprise remediation Phase 3.1).

Consolidates what used to be copy-pasted into every service's main.py:
  - a request correlation id (accept inbound X-Correlation-ID or mint one),
  - baseline security response headers,
  - opt-in structured JSON logging that carries the correlation id.

Usage in a service's main.py:
    from gdb_common.observability import install_observability
    install_observability(app)            # after `app = FastAPI(...)`

Integration/httpx clients read `current_correlation_id()` to forward the id.
"""

from __future__ import annotations

import json
import logging
import os
import uuid
from contextvars import ContextVar

# The single correlation-id context for the in-flight request.
correlation_id_ctx: ContextVar[str] = ContextVar("correlation_id", default="-")


def current_correlation_id() -> str:
    """Correlation id for the current request ('-' outside a request)."""
    return correlation_id_ctx.get()


def new_correlation_id() -> str:
    """Generate a fresh random correlation id (32-char hex)."""
    return uuid.uuid4().hex


class CorrelationIdFilter(logging.Filter):
    """Injects the current correlation id onto every log record."""

    def filter(self, record: logging.LogRecord) -> bool:  # noqa: A003
        """Attach the current correlation id to the record; never drop the record."""
        record.correlation_id = correlation_id_ctx.get()
        return True


class JsonFormatter(logging.Formatter):
    """Minimal structured-JSON log formatter."""

    def format(self, record: logging.LogRecord) -> str:
        """Serialize a log record to a single JSON line.

        Args:
            record: The log record to render.

        Returns:
            A JSON string with timestamp, level, logger, message, correlation
            id, and (when present) a formatted exception traceback.
        """
        payload = {
            "ts": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "correlation_id": getattr(record, "correlation_id", "-"),
        }
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def configure_json_logging(level: str = "INFO") -> None:
    """Route root logging through a single JSON handler with the correlation id."""
    handler = logging.StreamHandler()
    handler.addFilter(CorrelationIdFilter())
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.setLevel(level)
    root.handlers = [handler]


def install_observability(app, *, json_logs: bool | None = None):
    """Register the correlation + security-headers middleware and (opt-in) JSON logs.

    json_logs: None -> honour the LOG_FORMAT=json env var; True/False -> force.
    """

    @app.middleware("http")
    async def _observability(request, call_next):
        """Set the correlation id for the request and add baseline security headers.

        Reuses an inbound X-Correlation-ID or mints a new one, binds it to the
        request context, echoes it on the response, and sets standard security
        headers if not already present.
        """
        cid = request.headers.get("X-Correlation-ID") or new_correlation_id()
        correlation_id_ctx.set(cid)
        response = await call_next(request)
        response.headers["X-Correlation-ID"] = cid
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        response.headers.setdefault(
            "Strict-Transport-Security", "max-age=31536000; includeSubDomains"
        )
        return response

    if json_logs is None:
        json_logs = os.getenv("LOG_FORMAT", "").strip().lower() == "json"
    if json_logs:
        configure_json_logging()

    return app
