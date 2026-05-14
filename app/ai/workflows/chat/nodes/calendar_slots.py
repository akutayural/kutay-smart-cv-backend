from collections import defaultdict
from datetime import datetime
from zoneinfo import ZoneInfo

from app.core.config import get_settings
from app.core.logging import get_logger
from app.integrations.calendar.service import CalendarService

logger = get_logger(__name__)



def format_slot(start: str, end: str, timezone: str) -> str:
    tz = ZoneInfo(timezone)

    start_dt = datetime.fromisoformat(start).astimezone(tz)
    end_dt = datetime.fromisoformat(end).astimezone(tz)

    return (
        f"{start_dt.strftime('%A, %d %B %Y')} "
        f"{start_dt.strftime('%H:%M')}–{end_dt.strftime('%H:%M')}"
    )


def slot_to_dict(slot) -> dict:
    return {
        "start": slot.start,
        "end": slot.end,
        "timezone": slot.timezone,
    }


def get_available_slots(days: int = 7, duration_minutes: int = 60) -> list[dict]:
    service = CalendarService()

    availability = service.get_available_slots(
        days=days,
        duration_minutes=duration_minutes,
    )

    logger.info(
        "calendar_service_available_slots_debug",
        total=len(availability.slots),
        slots=[
            {
                "start": slot.start,
                "end": slot.end,
                "timezone": slot.timezone,
            }
            for slot in availability.slots[:50]
        ],
    )

    return [slot_to_dict(slot) for slot in availability.slots]


def group_slots_by_day(slots: list[dict]) -> dict[str, list[dict]]:
    grouped = defaultdict(list)

    for slot in slots:
        timezone = slot["timezone"]
        tz = ZoneInfo(timezone)
        start_dt = datetime.fromisoformat(slot["start"]).astimezone(tz)
        day_key = start_dt.strftime("%A, %d %B %Y")
        grouped[day_key].append(slot)

    return dict(grouped)


def build_day_summary_answer(slots: list[dict]) -> str:
    settings = get_settings()

    if not slots:
        return (
            "I could not find available meeting slots in Kutay's calendar "
            "for the next 7 days."
        )

    grouped = group_slots_by_day(slots)

    lines = [
        f"Kutay has the following available meeting times in {settings.calendar_timezone}:"
    ]

    for day, day_slots in grouped.items():
        times = []

        for slot in day_slots[:4]:
            tz = ZoneInfo(slot["timezone"])
            start_dt = datetime.fromisoformat(slot["start"]).astimezone(tz)
            times.append(start_dt.strftime("%H:%M"))

        lines.append(f"- {day}: {', '.join(times)}")

    lines.append("")
    lines.append("Which day/time works best for you? You can also type a specific time like 'Tuesday at 2pm'.")
    return "\n".join(lines)
