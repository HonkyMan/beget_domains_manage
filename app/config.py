"""Application configuration."""

from functools import lru_cache
from pathlib import Path
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
