import json
from functools import lru_cache
from typing import Literal, TypedDict

from openai import AsyncOpenAI, OpenAI

from app.core.config import get_settings
from app.core.logging import get_logger
from app.ai.guardrails.known_entities import KNOWN_ENTITIES
from app.ai.guardrails.scope_prompts import SCOPE_CLASSIFIER_SYSTEM_PROMPT

logger = get_logger(__name__)

AllowedIntent = Literal[
    "professional_background",
    "skills",
    "projects",
    "experience",
    "education",
    "role_fit",
    "availability",
    "visa",
    "personal_context",
    "hobbies",
    "work_style",
    "values",
    "meeting_availability",
    "meeting_scheduling",
    "meeting_confirmation",
    "out_of_scope",
]


class UnderstandingResult(TypedDict):
    allowed: bool
    reason: str | None
    intent: AllowedIntent
    rewritten_question: str | None
    active_entity: str | None


GENERIC_REFUSAL = (
    "I can only answer questions about Kutay's experience, projects, skills, "
    "education, availability, visa status, role fit, or meeting scheduling."
)

DIRECT_DENY_TERMS = {
    "weather",
    "football",
    "soccer",
    "politics",
    "religion",
    "stock price",
    "bitcoin price",
    "crypto price",
    "news",
    "recipe",
    "movie",
    "song",
    "celebrity",
    "travel",
}


def _normalize(message: str) -> str:
    return (
        message.lower()
        .replace("open-source", "open source")
        .replace("open_source", "open source")
        .replace("api-exception", "apiexception")
        .replace("api_exception", "apiexception")
        .replace("kutay'in", "kutay")
        .replace("kutayın", "kutay")
        .replace("kutayin", "kutay")
        .strip()
    )


def _format_known_entities() -> str:
    parts = []

    for entity_type, entities in KNOWN_ENTITIES.items():
        if entities:
            parts.append(f"{entity_type.title()}: {', '.join(entities)}")

    return "\n".join(parts)


def _fallback_understanding() -> UnderstandingResult:
    return {
        "allowed": False,
        "reason": GENERIC_REFUSAL,
        "intent": "out_of_scope",
        "rewritten_question": None,
        "active_entity": None,
    }


def _is_direct_deny(message: str) -> bool:
    return any(term in message for term in DIRECT_DENY_TERMS)


def _build_user_prompt(
    message: str,
    conversation_context: str | None = None,
    conversation_memory: str | None = None,
    active_entity: str | None = None,
) -> str:
    return f"""
Known Kutay-related entities:
{_format_known_entities()}

Conversation memory:
{conversation_memory or "No conversation memory provided."}

Conversation context:
{conversation_context or "No prior context provided."}

Current active entity:
{active_entity or "None"}

Current user message:
{message}
""".strip()


def _parse_understanding_result(
    result: dict,
    original_message: str,
) -> UnderstandingResult:
    allowed = bool(result.get("allowed", False))
    intent = result.get("intent", "out_of_scope")

    if intent not in AllowedIntent.__args__:
        intent = "out_of_scope"

    rewritten_question = result.get("rewritten_question") or original_message
    active_entity = result.get("active_entity")

    if not allowed or intent == "out_of_scope":
        return _fallback_understanding()

    return {
        "allowed": True,
        "reason": None,
        "intent": intent,
        "rewritten_question": rewritten_question,
        "active_entity": active_entity,
    }


@lru_cache(maxsize=512)
def _understand_with_llm_cached(
    message: str,
    conversation_context: str | None,
    conversation_memory: str | None,
    active_entity: str | None,
) -> dict:
    settings = get_settings()
    client = OpenAI(api_key=settings.openai_api_key)

    response = client.chat.completions.create(
        model=settings.scope_classifier_model,
        messages=[
            {"role": "system", "content": SCOPE_CLASSIFIER_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": _build_user_prompt(
                    message=message,
                    conversation_context=conversation_context,
                    conversation_memory=conversation_memory,
                    active_entity=active_entity,
                ),
            },
        ],
        temperature=0,
        max_tokens=settings.max_scope_classifier_tokens,
        response_format={"type": "json_object"},
    )

    raw = response.choices[0].message.content or "{}"
    return json.loads(raw)


async def _understand_with_llm_async(
    message: str,
    conversation_context: str | None,
    conversation_memory: str | None,
    active_entity: str | None,
) -> dict:
    settings = get_settings()
    client = AsyncOpenAI(api_key=settings.openai_api_key)

    response = await client.chat.completions.create(
        model=settings.scope_classifier_model,
        messages=[
            {"role": "system", "content": SCOPE_CLASSIFIER_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": _build_user_prompt(
                    message=message,
                    conversation_context=conversation_context,
                    conversation_memory=conversation_memory,
                    active_entity=active_entity,
                ),
            },
        ],
        temperature=0,
        max_tokens=settings.max_scope_classifier_tokens,
        response_format={"type": "json_object"},
    )

    raw = response.choices[0].message.content or "{}"
    return json.loads(raw)


def understand_message(
    message: str,
    conversation_context: str | None = None,
    conversation_memory: str | None = None,
    active_entity: str | None = None,
) -> UnderstandingResult:
    normalized = _normalize(message)

    if not normalized:
        return _fallback_understanding()

    if _is_direct_deny(normalized):
        return _fallback_understanding()

    settings = get_settings()

    if not settings.scope_classifier_enabled:
        return _fallback_understanding()

    try:
        result = _understand_with_llm_cached(
            normalized,
            conversation_context,
            conversation_memory,
            active_entity,
        )
    except Exception as exc:
        logger.exception(
            "conversation_understanding_failed",
            error_type=type(exc).__name__,
        )
        return _fallback_understanding()

    return _parse_understanding_result(result, original_message=message)


async def understand_message_async(
    message: str,
    conversation_context: str | None = None,
    conversation_memory: str | None = None,
    active_entity: str | None = None,
) -> UnderstandingResult:
    normalized = _normalize(message)

    if not normalized:
        return _fallback_understanding()

    if _is_direct_deny(normalized):
        return _fallback_understanding()

    settings = get_settings()

    if not settings.scope_classifier_enabled:
        return _fallback_understanding()

    try:
        result = await _understand_with_llm_async(
            normalized,
            conversation_context,
            conversation_memory,
            active_entity,
        )
    except Exception as exc:
        logger.exception(
            "async_conversation_understanding_failed",
            error_type=type(exc).__name__,
        )
        return _fallback_understanding()

    return _parse_understanding_result(result, original_message=message)
