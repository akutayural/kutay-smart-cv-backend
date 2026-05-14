import asyncio

from app.core.logging import get_logger
from app.integrations.calendar.schemas import CreateMeetingRequest
from app.integrations.calendar.service import CalendarService
from app.ai.workflows.chat.state import ChatState

logger = get_logger(__name__)


def _create_meeting_from_state(state: ChatState):

    email = state.get("meeting_email")
    purpose = state.get("meeting_purpose")
    selected_slot = state.get("meeting_selected_slot")

    if not email or not purpose:
        return None, (
            "I do not have enough meeting details yet. "
            "Please provide attendee email and meeting purpose."
        )

    if not selected_slot:
        return None, (
            "I have the meeting details, but I need a specific selected slot before scheduling. "
            "Please choose one of the suggested slots."
        )

    service = CalendarService()

    result = service.create_meeting(
        CreateMeetingRequest(
            attendee_email=email,
            purpose=purpose,
            start=selected_slot["start"],
            end=selected_slot["end"],
            timezone=selected_slot["timezone"],
        )
    )

    return result, None


async def calendar_confirmation_node(state: ChatState) -> ChatState:
    logger.info(
        "calendar_confirmation_started",
        question=state["question"][:120],
        meeting_ready_to_schedule=state.get("meeting_ready_to_schedule"),
        meeting_selected_slot=state.get("meeting_selected_slot"),
    )

    if not state.get("meeting_ready_to_schedule"):
        return {
            **state,
            "documents": [],
            "answer": (
                "I cannot schedule the meeting yet because the meeting details are incomplete. "
                "Please choose a specific slot and provide attendee email and meeting purpose."
            ),
            "stream_ready": False,
        }

    result, error_message = await asyncio.to_thread(
        _create_meeting_from_state,
        state,
    )

    if error_message:
        return {
            **state,
            "documents": [],
            "answer": error_message,
            "stream_ready": False,
        }

    answer = (
        "The meeting has been scheduled successfully.\n\n"
        f"- Summary: {result.summary}\n"
        f"- Calendar link: {result.html_link}"
    )

    logger.info(
        "calendar_confirmation_completed",
        event_id=result.event_id,
    )

    return {
        **state,
        "documents": [],
        "meeting_flow_active": False,
        "meeting_email": None,
        "meeting_purpose": None,
        "meeting_requested_start": None,
        "meeting_requested_end": None,
        "meeting_candidate_slots": [],
        "meeting_selected_slot": None,
        "meeting_ready_to_schedule": False,
        "answer": answer,
        "stream_ready": False,
    }
