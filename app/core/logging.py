"""Structured JSON logging with request/conversation context.

We use ``structlog`` because it gives us context-bound loggers that play well
with FastAPI request middleware: every log line emitted during a request will
automatically carry ``request_id`` and ``conversation_id`` if they were bound.
"""

from __future__ import annotations

import logging
import sys
from typing import Any

import structlog
from structlog.contextvars import merge_contextvars

from app.core.config import Settings


def configure_logging(settings: Settings) -> None:
    """Configure stdlib logging + structlog.

    Idempotent: safe to call multiple times (e.g. tests).
    """
    level = getattr(logging, settings.app_log_level.upper(), logging.INFO)

    # Reset handlers to keep things deterministic across reloads.
    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(level)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    handler.setFormatter(logging.Formatter("%(message)s"))
    root.addHandler(handler)

    # Quiet noisy loggers in production.
    for noisy in ("uvicorn.access", "sqlalchemy.engine.Engine"):
        logging.getLogger(noisy).setLevel(
            logging.WARNING if settings.is_production else logging.INFO
        )

    processors: list[Any] = [
        merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if settings.app_env == "local":
        processors.append(structlog.dev.ConsoleRenderer(colors=True))
    else:
        processors.append(structlog.processors.JSONRenderer())

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(level),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """Return a context-aware structured logger."""
    return structlog.get_logger(name)
