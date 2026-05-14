from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Kutay Smart CV AI"
    environment: str = "development"
    app_log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(default="INFO")
    app_env: Literal["local", "dev", "staging", "prod"] = Field(default="local")


    openai_api_key: str
    openai_chat_model: str = "gpt-4o-mini"
    openai_embedding_model: str = "text-embedding-3-small"

    qdrant_url: str
    qdrant_api_key: str
    qdrant_collection: str = "kutay_smart_cv"

    allowed_origins: str = "http://localhost:3000"
    rate_limit: str = "5/minute"

    max_context_chunks: int = 5
    max_output_tokens: int = 220

    scope_classifier_enabled: bool = True
    scope_classifier_model: str = "gpt-4o-mini"
    max_scope_classifier_tokens: int = 80

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    redis_url: str
    conversation_ttl_seconds: int = 3600

    # Calendar tool settings
    google_calendar_token_path: str | None = None
    google_calendar_credentials_path: str | None = None
    google_calendar_scopes: list[str] = []
    calendar_timezone: str = "Europe/London"
    calendar_workday_start_hour: int = 9
    calendar_workday_end_hour: int = 18

    @property
    def allowed_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]

    @property
    def is_production(self) -> bool:
        return self.app_env == "prod"


@lru_cache
def get_settings() -> Settings:
    return Settings()

