from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from app.core.config import get_settings


class CalendarClient:
    def __init__(self):
        self.settings = get_settings()
        self._client = None

    def _load_credentials(self) -> Credentials:
        credentials = Credentials.from_authorized_user_file(
            Path(self.settings.google_calendar_token_path),
            self.settings.google_calendar_scopes,
        )

        if credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())

        return credentials

    def get_client(self):
        if self._client is None:
            self._client = build(
                "calendar",
                "v3",
                credentials=self._load_credentials(),
            )

        return self._client
