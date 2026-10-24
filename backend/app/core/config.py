"""Settings via pydantic-settings (D15). Values come from backend/.env;
only .env.example is committed. Variable names locked in HWGA01."""

from functools import lru_cache
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    database_url: str = "postgresql+psycopg://hwga:hwga@127.0.0.1:55432/hwga"
    test_database_url: str | None = None
    media_storage_root: Path = Path("data/media")
    auth_token_pepper: str = ""
    user_timezone: str = "Asia/Kolkata"
    gemini_api_key: str | None = None
    scheduler_enabled: bool = False
    log_level: str = "INFO"

    @field_validator("user_timezone")
    @classmethod
    def _iana_timezone(cls, v: str) -> str:
        try:
            ZoneInfo(v)
        except ZoneInfoNotFoundError as exc:
            raise ValueError(f"USER_TIMEZONE is not a valid IANA name: {v!r}") from exc
        return v

    @model_validator(mode="after")
    def _test_db_is_isolated(self) -> "Settings":
        if self.test_database_url and self.test_database_url == self.database_url:
            raise ValueError(
                "TEST_DATABASE_URL must differ from DATABASE_URL; "
                "tests never point at the dev dataset (TRD §6.5)"
            )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
