from fastapi import APIRouter

from app.api.v1.routes.chat import router as chat_router
from app.api.v1.routes.health import router as health_router
from app.api.v1.routes.metrics import router as metrics_router

api_router = APIRouter()

api_router.include_router(chat_router)
api_router.include_router(health_router)
api_router.include_router(metrics_router)
