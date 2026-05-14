from app.integrations.calendar.client import CalendarClient


def test_calendar_client_creation():
    client = CalendarClient().get_client()

    assert client is not None
