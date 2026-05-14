"""Domain exceptions and FastAPI exception handlers.

Centralising error translation here ensures we never leak raw stack traces or
SQLAlchemy errors to API clients. Every exception is mapped to a stable JSON
shape: ``{"error": {"code": str, "message": str, "request_id": str}}``.
"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.logging import get_logger

logger = get_logger(__name__)


# --------------------------------------------------------------------- Domain
class AppError(Exception):
    """Base application exception. Subclasses set ``status_code`` and ``code``."""

    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    code: str = "internal_error"
    message: str = "An unexpected error occurred."

    def __init__(self, message: str | None = None, *, details: dict[str, Any] | None = None):
        super().__init__(message or self.message)
        if message:
            self.message = message
        self.details = details or {}


class NotFoundError(AppError):
    status_code = status.HTTP_404_NOT_FOUND
    code = "not_found"
    message = "The requested resource was not found."


class UnauthorizedError(AppError):
    status_code = status.HTTP_401_UNAUTHORIZED
    code = "unauthorized"
    message = "Authentication required."


class ForbiddenError(AppError):
    status_code = status.HTTP_403_FORBIDDEN
    code = "forbidden"
    message = "You do not have permission to access this resource."


class ValidationError(AppError):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    code = "validation_error"
    message = "Request validation failed."


class RateLimitedError(AppError):
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    code = "rate_limited"
    message = "Too many requests. Please try again later."


class UpstreamError(AppError):
    """An upstream provider (LLM, DB) failed in a way we cannot recover from."""

    status_code = status.HTTP_502_BAD_GATEWAY
    code = "upstream_error"
    message = "Upstream service is unavailable."


class ToolExecutionError(AppError):
    """A tool failed during execution. The LLM should be told politely."""

    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    code = "tool_execution_error"
    message = "A tool failed to execute."


# ----------------------------------------------------------------- Handlers
def _request_id(request: Request) -> str:
    return getattr(request.state, "request_id", "")


def _error_payload(code: str, message: str, request_id: str) -> dict[str, Any]:
    return {"error": {"code": code, "message": message, "request_id": request_id}}


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    rid = _request_id(request)
    logger.warning(
        "app_error",
        code=exc.code,
        message=exc.message,
        status_code=exc.status_code,
        details=exc.details,
        request_id=rid,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=_error_payload(exc.code, exc.message, rid),
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    rid = _request_id(request)
    return JSONResponse(
        status_code=exc.status_code,
        content=_error_payload(
            code=f"http_{exc.status_code}",
            message=str(exc.detail) if exc.detail else "HTTP error",
            request_id=rid,
        ),
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    rid = _request_id(request)
    logger.info("validation_error", errors=exc.errors(), request_id=rid)
    details = [
        {k: str(v) if not isinstance(v, (str, int, float, bool, list, dict, type(None))) else v
         for k, v in err.items() if k != "ctx"}
        for err in exc.errors()
    ]
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            **_error_payload("validation_error", "Request validation failed.", rid),
            "details": details,
        },
    )


async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    rid = _request_id(request)
    # We intentionally do NOT include the raw error message; SQL errors can
    # leak schema details, table names, and even data values.
    logger.exception("database_error", request_id=rid, error_type=type(exc).__name__)
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content=_error_payload(
            "database_unavailable",
            "A database error occurred. Please try again.",
            rid,
        ),
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    rid = _request_id(request)
    logger.exception("unhandled_exception", request_id=rid, error_type=type(exc).__name__)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=_error_payload("internal_error", "An unexpected error occurred.", rid),
    )


def install_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, app_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, unhandled_exception_handler)
