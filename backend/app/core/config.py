from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        enable_decoding=False,
    )

    app_name: str = "Studio Booking MVP"
    environment: str = "development"
    debug: bool = True
    api_prefix: str = "/api/v1"
    database_url: str = "sqlite+aiosqlite:///./studio.db"

    telegram_bot_token: str = "000000:dev-token"
    telegram_admin_chat_ids: list[int] = Field(default_factory=list)
    admin_telegram_ids: list[int] = Field(default_factory=list)

    auth_secret: str = "studio-dev-secret"
    session_ttl_minutes: int = 720

    studio_timezone: str = "Europe/Moscow"
    slot_step_minutes: int = 30
    allow_dev_login: bool = True
    allow_schema_create: bool = True
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173", "http://127.0.0.1:5173"])

    @field_validator("telegram_admin_chat_ids", "admin_telegram_ids", mode="before")
    @classmethod
    def parse_int_list(cls, value: object) -> list[int]:
        if value in (None, "", []):
            return []
        if isinstance(value, str):
            return [int(item.strip()) for item in value.split(",") if item.strip()]
        if isinstance(value, list):
            return [int(item) for item in value]
        raise TypeError("List of integers expected")

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_str_list(cls, value: object) -> list[str]:
        if value in (None, "", []):
            return []
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        if isinstance(value, list):
            return [str(item) for item in value]
        raise TypeError("List of strings expected")


@lru_cache
def get_settings() -> Settings:
    return Settings()
