"""Application configuration."""

from functools import lru_cache
from pathlib import Path
from typing import Any
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Telegram
    telegram_bot_token: str
    admin_chat_id: int

    # Beget API
    beget_login: str
    beget_password: str

    # Optional
    log_level: str = "INFO"

    # Paths
    data_dir: Path = Path("data")

    @field_validator('admin_chat_id', mode='before')
    @classmethod
    def validate_admin_chat_id(cls, v: Any) -> int:
        """Validate and convert admin_chat_id."""
        if v is None or v == '' or (isinstance(v, str) and v.strip() == ''):
            raise ValueError(
                "ADMIN_CHAT_ID environment variable is not set or empty. "
                "Please set it in Portainer Environment Variables (e.g., ADMIN_CHAT_ID=123456789)"
            )
        try:
            return int(v)
        except (ValueError, TypeError):
            raise ValueError(
                f"ADMIN_CHAT_ID must be a valid integer (your Telegram user ID), got: {v!r}"
            )

    @field_validator('telegram_bot_token', mode='before')
    @classmethod
    def validate_telegram_bot_token(cls, v: Any) -> str:
        """Validate telegram_bot_token is not empty."""
        if v is None or v == '' or (isinstance(v, str) and v.strip() == ''):
            raise ValueError(
                "TELEGRAM_BOT_TOKEN environment variable is not set or empty. "
                "Please set it in Portainer Environment Variables. "
                "Get your token from @BotFather in Telegram (format: 1234567890:ABCdefGHIjklMNOpqrsTUVwxyz)"
            )
        token = v.strip()
        # Basic format check: should contain ':' and be reasonable length
        if ':' not in token or len(token) < 30:
            raise ValueError(
                f"TELEGRAM_BOT_TOKEN appears invalid. Expected format: 1234567890:ABCdefGHIjklMNOpqrsTUVwxyz, got: {token[:20]}..."
            )
        return token

    @field_validator('beget_login', 'beget_password', mode='before')
    @classmethod
    def validate_beget_credentials(cls, v: Any, info) -> str:
        """Validate Beget credentials are not empty."""
        field_name = info.field_name.upper()
        if v is None or v == '' or (isinstance(v, str) and v.strip() == ''):
            raise ValueError(
                f"{field_name} environment variable is not set or empty. "
                f"Please set it in Portainer Environment Variables with your Beget account credentials."
            )
        return v.strip()

    @property
    def db_path(self) -> Path:
        """Path to SQLite database file."""
        return self.data_dir / "bot.db"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance.
    
    This function returns a singleton Settings instance.
    Use this instead of creating Settings() directly.
    """
    return Settings()
