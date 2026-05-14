from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.middleware import SlowAPIMiddleware

from app.api.v1 import api_router
from app.core.config import Settings, get_settings
from app.core.exceptions import install_exception_handlers
from app.core.logging import configure_logging, get_logger
from app.core.middleware import RequestContextMiddleware
from app.core.rate_limit import limiter
from api_exception import register_exception_handlers


logger = get_logger(__name__)

API_V1_PREFIX = "/api/v1"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings: Settings = app.state.settings

    logger.info(
        "startup_complete",
        env=settings.app_env,
    )

    try:
        yield
    finally:
        logger.info("shutdown_complete")


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()

    configure_logging(settings)

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        debug=settings.app_env == "local",
        docs_url="/docs" if not settings.is_production else None,
        redoc_url=None,
        openapi_url="/openapi.json" if not settings.is_production else None,
        lifespan=lifespan,
    )

    register_exception_handlers(
        app,
        log=True,
        log_traceback=True,
        log_request_context=True,
        log_header_keys=("x-request-id", "x-correlation-id", "user-agent"),
        extra_log_fields={"service": "kutay-smart-cv-api"},
        response_headers=True,
    )

    app.state.settings = settings

    app.state.limiter = limiter

    app.add_middleware(SlowAPIMiddleware)
    app.add_middleware(RequestContextMiddleware)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=[
            "Authorization",
            "Content-Type",
            "X-Request-ID",
            "X-Conversation-ID",
        ],
        expose_headers=[
            "X-Request-ID",
            "X-Conversation-ID",
        ],
    )

    install_exception_handlers(app)

    app.include_router(api_router, prefix=API_V1_PREFIX)

    return app


app = create_app()
