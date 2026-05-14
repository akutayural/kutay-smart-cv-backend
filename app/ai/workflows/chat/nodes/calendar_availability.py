import asyncio

from app.core.logging import get_logger
from app.ai.workflows.chat.nodes.calendar_slots import (
    build_day_summary_answer,
    get_available_slots,
)
from app.ai.workflows.chat.state import ChatState

logger = get_logger(__name__)


def build_availability_answer(state: ChatState) -> tuple[str, list[dict]]:
    slots = get_available_slots(days=7, duration_minutes=60)
    return build_day_summary_answer(slots), slots


async def calendar_availability_node(state: ChatState) -> ChatState:
    logger.info(
        "calendar_availability_started",
        question=state["question"][:120],
        intent=state.get("intent"),
    )

    answer, slots = await asyncio.to_thread(
        build_availability_answer,
        state,
    )

    logger.info(
        "calendar_availability_completed",
        intent=state.get("intent"),
        slot_count=len(slots),
    )

    return {
        **state,
        "documents": [],
        "meeting_flow_active": True,
        "meeting_candidate_slots": slots,
        "meeting_selected_slot": None,
        "meeting_requested_start": None,
        "meeting_requested_end": None,
        "meeting_ready_to_schedule": False,
        "answer": answer,
        "stream_ready": False,
    }
