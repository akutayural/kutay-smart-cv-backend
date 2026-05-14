import time
from contextlib import contextmanager
from collections.abc import Generator

from app.observability.events import track_event


@contextmanager
def track_timing(
    metric_name: str,
    **metadata,
) -> Generator[None, None, None]:
    start = time.perf_counter()

    try:
        yield

    finally:
        elapsed_ms = round(
            (time.perf_counter() - start) * 1000,
            2,
        )

        track_event(
            metric_name,
            elapsed_ms=elapsed_ms,
            **metadata,
        )
