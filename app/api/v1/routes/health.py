from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.core.config import Settings, get_settings
from app.core.qdrant import qdrant_client
from app.core.redis import redis_client
from app.schemas.health import DependencyStatus, HealthResponse, ReadinessResponse

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Liveness probe",
    status_code=status.HTTP_200_OK,
)
async def health(settings: Annotated[Settings, Depends(get_settings)]) -> HealthResponse:
    return HealthResponse(
        status="ok",
        service=settings.app_name,
        version="0.1.0",
    )


@router.get(
    "/ready",
    response_model=ReadinessResponse,
    summary="Readiness probe",
    status_code=status.HTTP_200_OK,
)
async def readiness_check(
    settings: Annotated[Settings, Depends(get_settings)],
) -> ReadinessResponse:
    overall_status = "ready"

    redis_status = DependencyStatus(status="ok")
    qdrant_status = DependencyStatus(status="ok")

    try:
        await redis_client.ping()
    except Exception as exc:
        overall_status = "degraded"
        redis_status = DependencyStatus(status="down", detail=str(exc))

    try:
        await qdrant_client.get_collections()
    except Exception as exc:
        overall_status = "degraded"
        qdrant_status = DependencyStatus(status="down", detail=str(exc))

    return ReadinessResponse(
        status=overall_status,
        service=settings.app_name,
        version="0.1.0",
        redis=redis_status,
        qdrant=qdrant_status,
    )
