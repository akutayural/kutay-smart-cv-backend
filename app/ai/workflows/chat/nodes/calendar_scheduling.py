import asyncio
import json
from datetime import datetime
from zoneinfo import ZoneInfo

from openai import AsyncOpenAI

from app.core.config import get_settings
from app.core.logging import get_logger
from app.ai.workflows.chat.nodes.calendar_slots import (
    build_day_summary_answer,
    format_slot,
    get_available_slots,
)
from app.ai.workflows.chat.state import ChatState

logger = get_logger(__name__)


def _current_london_datetime() -> str:
    return datetime.now(ZoneInfo("Europe/London")).isoformat()


def _meeting_extraction_system_prompt() -> str:
    return f"""
You extract meeting scheduling details from a user message.

Current datetime in Europe/London:
{_current_london_datetime()}

Return ONLY valid JSON:
{{
  "email": string | null,
  "purpose": string | null,
  "requested_start": string | null,
  "requested_end": string | null,
  "requested_day": string | null,
  "requested_time_range": "morning" | "afternoon" | "evening" | null,
  "slot_selection": integer | null,
  "asks_availability": boolean,
  "has_new_time_request": boolean
}}

Rules:
- Extract only explicitly provided meeting details.
- Do not invent email or purpose.
- Resolve relative dates using the current Europe/London datetime.
- If the user gives an exact date and time, return requested_start as ISO datetime with Europe/London offset.
- If duration is not provided, assume 60 minutes and set requested_end = requested_start + 60 minutes.
- If the user gives only a day/date, fill requested_day.
- If the user gives only a broad window, fill requested_time_range.
- If the user gives a day/date plus broad window, fill requested_day and requested_time_range.
- If candidate slots are provided and the user selects by number, return slot_selection.
- If candidate slots are provided and the user repeats the exact displayed slot time, return slot_selection.
- If the user selects an existing candidate slot, has_new_time_request must be false.
- asks_availability is true only when the user asks to see available slots.
- has_new_time_request is true only when the user gives a new date/day/time instead of selecting an existing candidate slot.
- If purpose is missing and the user sends a short phrase like "interview", "intro call", "technical interview", or "screening call", treat it as purpose.
- If email is already known, selected_slot is already known, and purpose is missing, interpret the current short non-email message as purpose.
""".strip()


def _build_extraction_prompt(
    message: str,
    state: ChatState,
) -> str:
    candidate_slots = state.get("meeting_candidate_slots") or []

    candidate_lines = []
    for index, slot in enumerate(candidate_slots, start=1):
        candidate_lines.append(
            f"{index}. {format_slot(slot['start'], slot['end'], slot['timezone'])}"
        )

    return f"""
Existing meeting state:
- meeting_flow_active: {state.get("meeting_flow_active", False)}
- email: {state.get("meeting_email") or "missing"}
- purpose: {state.get("meeting_purpose") or "missing"}
- requested_start: {state.get("meeting_requested_start") or "missing"}
- requested_end: {state.get("meeting_requested_end") or "missing"}
- selected_slot: {state.get("meeting_selected_slot") or "missing"}
- ready_to_schedule: {state.get("meeting_ready_to_schedule", False)}

Candidate slots:
{chr(10).join(candidate_lines) if candidate_lines else "No candidate slots."}

Current user message:
{message}
""".strip()


async def _extract_meeting_fields(
    message: str,
    state: ChatState,
) -> dict:
    settings = get_settings()
    client = AsyncOpenAI(api_key=settings.openai_api_key)

    response = await client.chat.completions.create(
        model=settings.scope_classifier_model,
        messages=[
            {
                "role": "system",
                "content": _meeting_extraction_system_prompt(),
            },
            {
                "role": "user",
                "content": _build_extraction_prompt(
                    message=message,
                    state=state,
                ),
            },
        ],
        temperature=0,
        max_tokens=260,
        response_format={"type": "json_object"},
    )

    raw = response.choices[0].message.content or "{}"

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        logger.warning("meeting_field_extraction_failed", raw=raw)
        payload = {}

    return {
        "email": payload.get("email"),
        "purpose": payload.get("purpose"),
        "requested_start": payload.get("requested_start"),
        "requested_end": payload.get("requested_end"),
        "requested_day": payload.get("requested_day"),
        "requested_time_range": payload.get("requested_time_range"),
        "slot_selection": payload.get("slot_selection"),
        "asks_availability": bool(payload.get("asks_availability")),
        "has_new_time_request": bool(payload.get("has_new_time_request")),
    }


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None

    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _same_instant_or_wall_time(a: datetime, b: datetime) -> bool:
    if a.tzinfo and b.tzinfo:
        return a.astimezone(ZoneInfo("Europe/London")) == b.astimezone(
            ZoneInfo("Europe/London")
        )

    return a.replace(tzinfo=None) == b.replace(tzinfo=None)


def _select_slot_from_candidate_slots(
    candidate_slots: list[dict],
    slot_selection,
) -> dict | None:
    if not candidate_slots or slot_selection is None:
        return None

    try:
        index = int(slot_selection) - 1
    except (TypeError, ValueError):
        return None

    if index < 0 or index >= len(candidate_slots):
        return None

    return candidate_slots[index]


def _availability_days_for_requested_start(
    requested_start: str | None,
    default_days: int = 7,
) -> int:
    requested_dt = _parse_dt(requested_start)

    if not requested_dt:
        return default_days

    now = datetime.now(ZoneInfo("Europe/London"))
    requested_dt = requested_dt.astimezone(ZoneInfo("Europe/London"))

    days_until_requested = (requested_dt.date() - now.date()).days

    return max(default_days, days_until_requested + 1)


def _find_exact_requested_slot(
    slots: list[dict],
    requested_start: str | None,
) -> dict | None:
    requested_start_dt = _parse_dt(requested_start)

    if not requested_start_dt:
        return None

    for slot in slots:
        slot_start = _parse_dt(slot.get("start"))

        if not slot_start:
            continue

        if _same_instant_or_wall_time(slot_start, requested_start_dt):
            return slot

    return None


def _slot_matches_day(
    slot: dict,
    requested_day: str | None,
) -> bool:
    if not requested_day:
        return True

    text = format_slot(
        slot["start"],
        slot["end"],
        slot["timezone"],
    ).lower()

    return requested_day.lower() in text


def _slot_matches_time_range(
    slot: dict,
    requested_time_range: str | None,
) -> bool:
    if not requested_time_range:
        return True

    requested = requested_time_range.lower()
    start_dt = datetime.fromisoformat(slot["start"]).astimezone(
        ZoneInfo(slot["timezone"])
    )

    windows = {
        "morning": range(8, 12),
        "afternoon": range(12, 17),
        "evening": range(17, 21),
    }

    for label, hours in windows.items():
        if label in requested:
            return start_dt.hour in hours

    return requested in start_dt.strftime("%H:%M").lower()


def _find_candidate_slots(
    slots: list[dict],
    requested_day: str | None,
    requested_time_range: str | None,
    limit: int = 5,
) -> list[dict]:
    matches = []

    for slot in slots:
        if not _slot_matches_day(slot, requested_day):
            continue

        if not _slot_matches_time_range(slot, requested_time_range):
            continue

        matches.append(slot)

        if len(matches) >= limit:
            break

    return matches


def _build_candidate_slots_answer(
    candidate_slots: list[dict],
    requested_day: str | None,
    requested_time_range: str | None,
) -> str:
    requested = " ".join(
        part for part in [requested_day, requested_time_range] if part
    ).strip()

    if not candidate_slots:
        return (
            f"I could not find an available slot for {requested or 'that time'}.\n\n"
            "Please choose another day and time range."
        )

    lines = [
        f"These slots are available for {requested}:" if requested else "These slots are available:",
        "",
    ]

    for index, slot in enumerate(candidate_slots, start=1):
        lines.append(
            f"{index}. {format_slot(slot['start'], slot['end'], slot['timezone'])}"
        )

    lines.extend(["", "Please choose one of these slots."])

    return "\n".join(lines)


def _build_exact_slot_unavailable_answer(
    requested_start: str | None,
) -> str:
    requested_dt = _parse_dt(requested_start)

    if requested_dt:
        requested_text = requested_dt.astimezone(
            ZoneInfo("Europe/London")
        ).strftime("%A, %d %B %Y %H:%M")

        return (
            f"I could not find an available slot for {requested_text}.\n\n"
            "Please choose another available time."
        )

    return (
        "I could not find that exact slot available.\n\n"
        "Please choose another available time."
    )


def _build_missing_slot_answer(
    candidate_slots: list[dict],
) -> str:
    if candidate_slots:
        lines = [
            "Please choose one of the suggested slots before I collect the remaining details:",
            "",
        ]

        for index, slot in enumerate(candidate_slots, start=1):
            lines.append(
                f"{index}. {format_slot(slot['start'], slot['end'], slot['timezone'])}"
            )

        return "\n".join(lines)

    return "Please choose a day and time range first, so I can suggest available slots."


def _build_selected_slot_answer(
    selected_slot: dict,
    missing_fields: list[str],
) -> str:
    lines = [
        f"Great. I selected {format_slot(selected_slot['start'], selected_slot['end'], selected_slot['timezone'])}."
    ]

    if missing_fields:
        lines.extend(
            [
                "",
                "Please share the following details: "
                + ", ".join(missing_fields)
                + ".",
            ]
        )

    return "\n".join(lines)


def _build_confirmation_answer(
    meeting_email: str,
    meeting_purpose: str,
    selected_slot: dict,
) -> str:
    return (
        "I have the meeting details:\n\n"
        f"- Attendee email: {meeting_email}\n"
        f"- Purpose: {meeting_purpose}\n"
        f"- Selected slot: {format_slot(selected_slot['start'], selected_slot['end'], selected_slot['timezone'])}\n\n"
        "Please confirm if I should proceed with scheduling this meeting."
    )


def _missing_fields(
    meeting_email: str | None,
    meeting_purpose: str | None,
    selected_slot: dict | None,
) -> list[str]:
    missing = []

    if not selected_slot:
        missing.append("selected slot")

    if not meeting_email:
        missing.append("attendee email")

    if not meeting_purpose:
        missing.append("meeting purpose")

    return missing


async def calendar_scheduling_node(state: ChatState) -> ChatState:
    logger.info(
        "calendar_scheduling_started",
        question=state["question"][:120],
        intent=state.get("intent"),
        meeting_email=state.get("meeting_email"),
        meeting_purpose=state.get("meeting_purpose"),
        meeting_requested_start=state.get("meeting_requested_start"),
        meeting_requested_end=state.get("meeting_requested_end"),
        meeting_selected_slot=state.get("meeting_selected_slot"),
    )

    extracted = await _extract_meeting_fields(
        message=state["question"],
        state=state,
    )

    logger.info(
        "calendar_scheduling_extracted",
        extracted=extracted,
    )

    meeting_email = extracted["email"] or state.get("meeting_email")
    meeting_purpose = extracted["purpose"] or state.get("meeting_purpose")

    candidate_slots = state.get("meeting_candidate_slots") or []
    selected_slot = state.get("meeting_selected_slot")

    selected_from_candidates = _select_slot_from_candidate_slots(
        candidate_slots=candidate_slots,
        slot_selection=extracted["slot_selection"],
    )

    if selected_from_candidates:
        selected_slot = selected_from_candidates
        candidate_slots = []
        requested_start = selected_slot["start"]
        requested_end = selected_slot["end"]
    elif extracted["has_new_time_request"]:
        selected_slot = None
        candidate_slots = []
        requested_start = extracted.get("requested_start")
        requested_end = extracted.get("requested_end")
    else:
        requested_start = (
            extracted.get("requested_start")
            or state.get("meeting_requested_start")
        )
        requested_end = (
            extracted.get("requested_end")
            or state.get("meeting_requested_end")
        )

    requested_day = extracted.get("requested_day")
    requested_time_range = extracted.get("requested_time_range")

    if selected_slot is None and requested_start:
        try:
            available_slots = await asyncio.to_thread(
                get_available_slots,
                _availability_days_for_requested_start(requested_start),
                60,
            )

            exact_slot = _find_exact_requested_slot(
                slots=available_slots,
                requested_start=requested_start,
            )

            if exact_slot:
                selected_slot = exact_slot
                candidate_slots = []
                requested_start = exact_slot["start"]
                requested_end = exact_slot["end"]
            else:
                answer = _build_exact_slot_unavailable_answer(requested_start)

                return {
                    **state,
                    "documents": [],
                    "meeting_flow_active": True,
                    "meeting_email": meeting_email,
                    "meeting_purpose": meeting_purpose,
                    "meeting_requested_start": requested_start,
                    "meeting_requested_end": requested_end,
                    "meeting_candidate_slots": [],
                    "meeting_selected_slot": None,
                    "meeting_ready_to_schedule": False,
                    "answer": answer,
                    "stream_ready": False,
                }
        except Exception as exc:
            logger.exception(
                "calendar_availability_lookup_failed",
                error_type=type(exc).__name__,
                error=str(exc),
            )

            return {
                **state,
                "answer": (
                    "I’m having trouble checking Kutay’s live calendar right now. "
                    "Please try again later or contact Kutay directly."
                ),
                "stream_ready": False,
                "meeting_flow_active": False,
            }

    if selected_slot is None and requested_day:
        try:
            available_slots = await asyncio.to_thread(
                get_available_slots,
                7,
                60,
            )

            candidate_slots = _find_candidate_slots(
                slots=available_slots,
                requested_day=requested_day,
                requested_time_range=requested_time_range,
                limit=5,
            )

            answer = _build_candidate_slots_answer(
                candidate_slots=candidate_slots,
                requested_day=requested_day,
                requested_time_range=requested_time_range,
            )

            return {
                **state,
                "documents": [],
                "meeting_flow_active": True,
                "meeting_email": meeting_email,
                "meeting_purpose": meeting_purpose,
                "meeting_requested_start": None,
                "meeting_requested_end": None,
                "meeting_candidate_slots": candidate_slots,
                "meeting_selected_slot": None,
                "meeting_ready_to_schedule": False,
                "answer": answer,
                "stream_ready": False,
            }
        except Exception as exc:
            logger.exception(
                "calendar_availability_lookup_failed",
                error_type=type(exc).__name__,
                error=str(exc),
            )

            return {
                **state,
                "answer": (
                    "I’m having trouble checking Kutay’s live calendar right now. "
                    "Please try again later or contact Kutay directly."
                ),
                "stream_ready": False,
                "meeting_flow_active": False,
            }

    if selected_slot is None and extracted["asks_availability"]:
        try:
            available_slots = await asyncio.to_thread(
                get_available_slots,
                7,
                60,
            )

            answer = build_day_summary_answer(available_slots)

            return {
                **state,
                "documents": [],
                "meeting_flow_active": True,
                "meeting_email": meeting_email,
                "meeting_purpose": meeting_purpose,
                "meeting_requested_start": None,
                "meeting_requested_end": None,
                "meeting_candidate_slots": available_slots,
                "meeting_selected_slot": None,
                "meeting_ready_to_schedule": False,
                "answer": answer,
                "stream_ready": False,
            }
        except Exception as exc:
            logger.exception(
                "calendar_availability_lookup_failed",
                error_type=type(exc).__name__,
                error=str(exc),
            )

            return {
                **state,
                "answer": (
                    "I’m having trouble checking Kutay’s live calendar right now. "
                    "Please try again later or contact Kutay directly."
                ),
                "stream_ready": False,
                "meeting_flow_active": False,
            }

    if selected_slot is None:
        try:
            available_slots = await asyncio.to_thread(
                get_available_slots,
                7,
                60,
            )

            answer = build_day_summary_answer(available_slots)

            return {
                **state,
                "documents": [],
                "meeting_flow_active": True,
                "meeting_email": meeting_email,
                "meeting_purpose": meeting_purpose,
                "meeting_requested_start": None,
                "meeting_requested_end": None,
                "meeting_candidate_slots": available_slots,
                "meeting_selected_slot": None,
                "meeting_ready_to_schedule": False,
                "answer": answer,
                "stream_ready": False,
            }
        except Exception as exc:
            logger.exception(
                "calendar_availability_lookup_failed",
                error_type=type(exc).__name__,
                error=str(exc),
            )

            return {
                **state,
                "answer": (
                    "I’m having trouble checking Kutay’s live calendar right now. "
                    "Please try again later or contact Kutay directly."
                ),
                "stream_ready": False,
                "meeting_flow_active": False,
            }

    missing_fields = _missing_fields(
        meeting_email=meeting_email,
        meeting_purpose=meeting_purpose,
        selected_slot=selected_slot,
    )

    if missing_fields:
        answer = _build_selected_slot_answer(
            selected_slot=selected_slot,
            missing_fields=missing_fields,
        )

        return {
            **state,
            "documents": [],
            "meeting_flow_active": True,
            "meeting_email": meeting_email,
            "meeting_purpose": meeting_purpose,
            "meeting_requested_start": selected_slot["start"],
            "meeting_requested_end": selected_slot["end"],
            "meeting_candidate_slots": [],
            "meeting_selected_slot": selected_slot,
            "meeting_ready_to_schedule": False,
            "answer": answer,
            "stream_ready": False,
        }

    answer = _build_confirmation_answer(
        meeting_email=meeting_email,
        meeting_purpose=meeting_purpose,
        selected_slot=selected_slot,
    )

    logger.info(
        "calendar_scheduling_completed",
        meeting_ready_to_schedule=True,
        meeting_email=meeting_email,
        meeting_purpose=meeting_purpose,
        meeting_selected_slot=selected_slot,
    )

    return {
        **state,
        "documents": [],
        "meeting_flow_active": True,
        "meeting_email": meeting_email,
        "meeting_purpose": meeting_purpose,
        "meeting_requested_start": selected_slot["start"],
        "meeting_requested_end": selected_slot["end"],
        "meeting_candidate_slots": [],
        "meeting_selected_slot": selected_slot,
        "meeting_ready_to_schedule": True,
        "answer": answer,
        "stream_ready": False,
    }
