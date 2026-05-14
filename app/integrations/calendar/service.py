from datetime import UTC, datetime, timedelta, time
from zoneinfo import ZoneInfo

from app.core.config import get_settings
from app.integrations.calendar.client import CalendarClient
from app.integrations.calendar.schemas import AvailabilityResponse, TimeSlot, CreateMeetingRequest, CreateMeetingResponse


class CalendarService:
    def __init__(self):
        self.settings = get_settings()
        self.client = CalendarClient().get_client()

    def list_upcoming_events(self, limit: int = 10) -> list[dict]:
        now = datetime.now(UTC).isoformat()

        result = (
            self.client.events()
            .list(
                calendarId="primary",
                timeMin=now,
                maxResults=limit,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )

        return result.get("items", [])

    def get_available_slots(
        self,
        days: int = 7,
        duration_minutes: int = 30,
    ) -> AvailabilityResponse:
        timezone = self.settings.calendar_timezone
        tz = ZoneInfo(timezone)

        now = datetime.now(tz)
        time_min = now.astimezone(UTC).isoformat()
        time_max = (now + timedelta(days=days)).astimezone(UTC).isoformat()

        events_result = (
            self.client.events()
            .list(
                calendarId="primary",
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )

        busy_slots: list[tuple[datetime, datetime]] = []

        for event in events_result.get("items", []):
            start_raw = event.get("start", {}).get("dateTime")
            end_raw = event.get("end", {}).get("dateTime")

            # Ignore all-day events such as birthdays.
            if not start_raw or not end_raw:
                continue

            busy_slots.append(
                (
                    datetime.fromisoformat(start_raw).astimezone(tz),
                    datetime.fromisoformat(end_raw).astimezone(tz),
                )
            )

        slots: list[TimeSlot] = []

        for day_offset in range(days):
            day = now.date() + timedelta(days=day_offset)

            if day.weekday() >= 5:
                continue

            work_start = datetime.combine(
                day,
                time(self.settings.calendar_workday_start_hour, 0),
                tzinfo=tz,
            )
            work_end = datetime.combine(
                day,
                time(self.settings.calendar_workday_end_hour, 0),
                tzinfo=tz,
            )

            cursor = max(now, work_start)

            if cursor.minute not in (0, 30):
                minutes_to_add = 30 - (cursor.minute % 30)
                cursor = cursor + timedelta(minutes=minutes_to_add)

            cursor = cursor.replace(second=0, microsecond=0)

            while cursor + timedelta(minutes=duration_minutes) <= work_end:
                slot_end = cursor + timedelta(minutes=duration_minutes)

                overlaps = any(
                    cursor < busy_end and slot_end > busy_start
                    for busy_start, busy_end in busy_slots
                )

                if not overlaps:
                    slots.append(
                        TimeSlot(
                            start=cursor.isoformat(),
                            end=slot_end.isoformat(),
                            timezone=timezone,
                        )
                    )

                cursor += timedelta(minutes=30)

        return AvailabilityResponse(slots=slots)


    def create_meeting(
        self,
        request: CreateMeetingRequest,
    ) -> CreateMeetingResponse:
        event = {
            "summary": f"Meeting with Kutay — {request.purpose}",
            "description": request.purpose,
            "start": {
                "dateTime": request.start,
                "timeZone": request.timezone,
            },
            "end": {
                "dateTime": request.end,
                "timeZone": request.timezone,
            },
            "attendees": [
                {
                    "email": request.attendee_email,
                }
            ],
            "conferenceData": {
                "createRequest": {
                    "requestId": f"kutay-smart-cv-{datetime.now().timestamp()}",
                    "conferenceSolutionKey": {
                        "type": "hangoutsMeet",
                    },
                },
            },
        }

        created = (
            self.client.events()
            .insert(
                calendarId="primary",
                body=event,
                sendUpdates="all",
                conferenceDataVersion=1,
            )
            .execute()
        )

        return CreateMeetingResponse(
            event_id=created["id"],
            summary=created.get("summary", event["summary"]),
            html_link=created.get("htmlLink"),
        )