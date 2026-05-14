from collections.abc import Mapping
from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)


def track_event(
    event_name: str,
    **payload: Any,
) -> None:
    logger.info(
        event_name,
        **payload,
    )


def track_error(
    event_name: str,
    error: Exception,
    extra: Mapping[str, Any] | None = None,
) -> None:
    logger.exception(
        event_name,
        error_type=type(error).__name__,
        error=str(error),
        **(extra or {}),
    )
