from pydantic import BaseModel, EmailStr


class TimeSlot(BaseModel):
    start: str
    end: str
    timezone: str


class AvailabilityResponse(BaseModel):
    slots: list[TimeSlot]


class CreateMeetingRequest(BaseModel):
    attendee_email: EmailStr
    purpose: str
    start: str
    end: str
    timezone: str


class CreateMeetingResponse(BaseModel):
    event_id: str
    summary: str
    html_link: str | None = None