from mcp.server.fastmcp import FastMCP

from app.integrations.calendar.service import CalendarService

mcp = FastMCP("kutay-calendar")


@mcp.tool()
def get_available_slots(
    days: int = 7,
    duration_minutes: int = 30,
) -> dict:
    """
    Get Kutay's available Google Calendar slots.
    """
    service = CalendarService()
    result = service.get_available_slots(
        days=days,
        duration_minutes=duration_minutes,
    )
    return result.model_dump()


@mcp.tool()
def list_upcoming_events(limit: int = 10) -> dict:
    """
    List Kutay's upcoming calendar events.
    """
    service = CalendarService()
    events = service.list_upcoming_events(limit=limit)

    return {
        "events": [
            {
                "summary": event.get("summary"),
                "start": event.get("start", {}),
                "end": event.get("end", {}),
            }
            for event in events
        ]
    }


if __name__ == "__main__":
    mcp.run()
