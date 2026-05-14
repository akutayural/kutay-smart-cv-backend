"""HTTP middleware.

* ``RequestContextMiddleware`` injects a per-request UUID and binds it (along
  with optional conversation/user IDs) into the structlog context so every log
  line emitted while the request is in flight carries the same trace IDs.

* ``CORSMiddleware`` is wired in ``main.py`` from FastAPI's standard middleware.
"""

from __future__ import annotations

import time
import uuid
from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from structlog.contextvars import bind_contextvars, clear_contextvars

from app.core.logging import get_logger

from app.observability.prometheus import REQUEST_COUNT, REQUEST_LATENCY

logger = get_logger(__name__)

REQUEST_ID_HEADER = "X-Request-ID"
CONVERSATION_ID_HEADER = "X-Conversation-ID"


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Bind request_id / conversation_id into log context and headers."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        request_id = request.headers.get(REQUEST_ID_HEADER) or str(uuid.uuid4())
        conversation_id = request.headers.get(CONVERSATION_ID_HEADER)

        request.state.request_id = request_id
        request.state.conversation_id = conversation_id

        clear_contextvars()
        bind_contextvars(
            request_id=request_id,
            conversation_id=conversation_id,
            method=request.method,
            path=request.url.path,
        )

        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            elapsed_ms = (time.perf_counter() - start) * 1000
            logger.exception("request_failed", elapsed_ms=round(elapsed_ms, 2))
            REQUEST_COUNT.labels(
                method=request.method,
                path=request.url.path,
            ).inc()
            raise
        else:
            elapsed_seconds = time.perf_counter() - start
            elapsed_ms = elapsed_seconds * 1000
            logger.info(
                "request_completed",
                status_code=response.status_code,
                elapsed_ms=round(elapsed_ms, 2),
            )
            REQUEST_COUNT.labels(
                method=request.method,
                path=request.url.path,
            ).inc()

            REQUEST_LATENCY.labels(
                method=request.method,
                path=request.url.path,
            ).observe(elapsed_seconds)
            response.headers[REQUEST_ID_HEADER] = request_id
            if conversation_id:
                response.headers[CONVERSATION_ID_HEADER] = conversation_id
            return response
        finally:
            clear_contextvars()
