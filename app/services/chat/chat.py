import json
from collections.abc import AsyncIterator

from langchain_openai import ChatOpenAI

from app.core.config import get_settings
from app.core.logging import get_logger
from app.services.chat.conversation_state import ConversationStateService
from app.ai.workflows.chat.streaming_workflow import build_initial_state, streaming_workflow
from app.ai.guardrails.output import validate_output
from app.ai.rag.prompts import SYSTEM_PROMPT
from app.observability import track_error, track_event, track_llm_usage, track_timing

HOLDBACK_CHARS = 160
logger = get_logger(__name__)


def _sse(event_type: str, content: str) -> str:
    payload = {
        "type": event_type,
        "content": content,
    }
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


def _build_conversation_context(
    conversation_state: dict | None,
) -> str:
    if not conversation_state:
        return ""

    parts = []

    last_question = conversation_state.get("last_question")
    last_answer = conversation_state.get("last_answer")

    if last_question:
        parts.append(f"Previous user message: {last_question}")

    if last_answer:
        parts.append(f"Previous assistant answer: {last_answer}")

    meeting_email = conversation_state.get("meeting_email")
    meeting_purpose = conversation_state.get("meeting_purpose")
    meeting_ready_to_schedule = conversation_state.get("meeting_ready_to_schedule")
    meeting_flow_active = conversation_state.get("meeting_flow_active")
    meeting_requested_start = conversation_state.get("meeting_requested_start")
    meeting_requested_end = conversation_state.get("meeting_requested_end")
    meeting_selected_slot = conversation_state.get("meeting_selected_slot")

    meeting_parts = []

    if meeting_email:
        meeting_parts.append(f"meeting_email={meeting_email}")

    if meeting_purpose:
        meeting_parts.append(f"meeting_purpose={meeting_purpose}")

    if meeting_ready_to_schedule is not None:
        meeting_parts.append(f"meeting_ready_to_schedule={meeting_ready_to_schedule}")

    if meeting_flow_active is not None:
        meeting_parts.append(f"meeting_flow_active={meeting_flow_active}")

    if meeting_requested_start:
        meeting_parts.append(f"meeting_requested_start={meeting_requested_start}")

    if meeting_requested_end:
        meeting_parts.append(f"meeting_requested_end={meeting_requested_end}")

    if meeting_selected_slot:
        meeting_parts.append(f"meeting_selected_slot={meeting_selected_slot}")

    if meeting_parts:
        parts.append("Meeting state: " + ", ".join(meeting_parts))

    return "\n".join(parts).strip()


def _build_conversation_memory(
    conversation_state: dict | None,
) -> str:
    if not conversation_state:
        return ""

    parts = []

    active_entity = conversation_state.get("active_entity")
    active_topic = conversation_state.get("active_topic")

    if active_entity:
        parts.append(f"Active entity: {active_entity}")

    if active_topic:
        parts.append(f"Active topic: {active_topic}")

    last_question = conversation_state.get("last_question")
    last_answer = conversation_state.get("last_answer")

    if last_question:
        parts.append(f"Last user question: {last_question}")

    if last_answer:
        parts.append(f"Last assistant answer: {last_answer}")

    return "\n".join(parts).strip()


async def _save_conversation_state(
    conversation_id: str | None,
    conversation_state: dict | None,
    question: str,
    state: dict,
    answer: str | None,
) -> None:
    if not conversation_id:
        return

    await ConversationStateService.set(
        conversation_id,
        {
            **(conversation_state or {}),
            "meeting_email": state.get("meeting_email"),
            "meeting_purpose": state.get("meeting_purpose"),
            "meeting_ready_to_schedule": state.get(
                "meeting_ready_to_schedule",
                False,
            ),
            "active_entity": state.get("active_entity"),
            "active_topic": state.get("active_topic"),
            "rewritten_question": state.get("rewritten_question"),
            "last_question": question,
            "last_answer": answer or state.get("answer", ""),
            "meeting_flow_active": state.get("meeting_flow_active", False),
            "meeting_requested_start": state.get("meeting_requested_start"),
            "meeting_requested_end": state.get("meeting_requested_end"),
            "meeting_candidate_slots": state.get("meeting_candidate_slots", []),
            "meeting_selected_slot": state.get("meeting_selected_slot"),
            "message_count": int(
                (conversation_state or {}).get("message_count", 0)
            ) + 1,
        },
    )


async def stream_chat_as_sse(
    question: str,
    conversation_id: str | None = None,
    conversation_state: dict | None = None,
) -> AsyncIterator[str]:
    settings = get_settings()

    conversation_context = _build_conversation_context(
        conversation_state,
    )

    conversation_memory = _build_conversation_memory(
        conversation_state,
    )

    initial_state = {
        **build_initial_state(question),
        **(conversation_state or {}),
        "question": question,
        "conversation_context": conversation_context,
        "conversation_memory": conversation_memory,
        "active_entity": (conversation_state or {}).get("active_entity"),
        "active_topic": (conversation_state or {}).get("active_topic"),
    }

    with track_timing(
            "chat_workflow_completed",
            conversation_id=conversation_id,
    ):
        state = await streaming_workflow.ainvoke(initial_state)

    if not state.get("stream_ready"):
        final_answer = state.get("answer") or "I cannot answer that question."

        await _save_conversation_state(
            conversation_id=conversation_id,
            conversation_state=conversation_state,
            question=question,
            state=state,
            answer=final_answer,
        )

        track_event(
            "chat_final_response_returned",
            conversation_id=conversation_id,
            intent=state.get("intent"),
            answer_chars=len(final_answer),
        )

        yield _sse("final", final_answer)
        return

    logger.info(
        "llm_stream_started",
        model=settings.openai_chat_model,
    )

    llm = ChatOpenAI(
        model=settings.openai_chat_model,
        api_key=settings.openai_api_key,
        temperature=0.1,
        max_tokens=settings.max_output_tokens,
        streaming=True,
    )

    full_answer = ""
    pending = ""
    last_validation_at = 0

    try:
        async for chunk in llm.astream(
            [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": state["prompt"]},
            ]
        ):
            token = chunk.content or ""
            if not isinstance(token, str) or not token:
                continue

            full_answer += token
            pending += token

            if len(full_answer) - last_validation_at >= 50:
                last_validation_at = len(full_answer)

                safe_so_far = validate_output(full_answer)

                if safe_so_far != full_answer.strip():
                    logger.warning(
                        "output_guardrail_triggered",
                    )

                    await _save_conversation_state(
                        conversation_id=conversation_id,
                        conversation_state=conversation_state,
                        question=question,
                        state=state,
                        answer=safe_so_far,
                    )

                    yield _sse("replace", safe_so_far)
                    return

            if len(pending) > HOLDBACK_CHARS:
                emit = pending[:-HOLDBACK_CHARS]
                pending = pending[-HOLDBACK_CHARS:]
                yield _sse("token", emit)

    except Exception as exc:
        logger.exception(
            "llm_stream_failed",
            error_type=type(exc).__name__,
        )
        track_error(
            "llm_stream_failed_observed",
            exc,
            {
                "conversation_id": conversation_id,
                "model": settings.openai_chat_model,
            },
        )
        yield _sse(
            "error",
            "Failed to stream response from LLM.",
        )
        yield _sse("done", "")
        return

    final_answer = validate_output(full_answer)

    if final_answer != full_answer.strip():
        await _save_conversation_state(
            conversation_id=conversation_id,
            conversation_state=conversation_state,
            question=question,
            state=state,
            answer=final_answer,
        )

        yield _sse("replace", final_answer)
        return

    if pending:
        yield _sse("token", pending)

    await _save_conversation_state(
        conversation_id=conversation_id,
        conversation_state=conversation_state,
        question=question,
        state=state,
        answer=final_answer,
    )

    logger.info(
        "llm_stream_completed",
        input_chars=len(question),
        total_chars=len(final_answer),
    )

    track_llm_usage(
        model=settings.openai_chat_model,
        input_text=state["prompt"],
        output_text=final_answer,
        metadata={
            "conversation_id": conversation_id,
            "intent": state.get("intent"),
        },
    )

    yield _sse("done", "")
