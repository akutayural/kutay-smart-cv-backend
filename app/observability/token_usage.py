from typing import Any

from app.observability.events import track_event


def estimate_token_usage(text: str) -> int:
    """
    Rough token estimation.
    OpenAI tokens are approximately ~4 chars/token.
    """
    if not text:
        return 0

    return max(1, len(text) // 4)


def track_llm_usage(
    *,
    model: str,
    input_text: str,
    output_text: str,
    metadata: dict[str, Any] | None = None,
) -> None:
    input_tokens = estimate_token_usage(input_text)
    output_tokens = estimate_token_usage(output_text)

    track_event(
        "llm_token_usage",
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=input_tokens + output_tokens,
        **(metadata or {}),
    )
