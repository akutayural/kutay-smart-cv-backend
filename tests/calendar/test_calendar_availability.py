from app.integrations.calendar.service import CalendarService


def test_calendar_availability():
    service = CalendarService()

    result = service.get_available_slots()

    assert result.slots is not None
    assert isinstance(result.slots, list)
