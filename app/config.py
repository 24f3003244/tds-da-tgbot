import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    BOT_TOKEN: str = "YOUR_TELEGRAM_BOT_TOKEN_HERE"
    OPENAI_API_KEY: str = "YOUR_OPENAI_API_KEY_HERE"
    OPENAI_MODEL: str = "gpt-4o-mini"
    PORT: int = 8000
    BASE_URL: str = "http://localhost:8000"
    PUBLIC_LOG_BASE_URL: str = "http://localhost:8000"
    LOG_DIRECTORY: str = "logs"
    DATA_CACHE_DIR: str = "cache"
    MAX_FILE_SIZE_MB: int = 50
    REQUEST_TIMEOUT: int = 30
    MAX_CONVERSATION_HISTORY: int = 20

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    def get_public_log_base_url(self) -> str:
        """Returns normalized public log base url without trailing slash."""
        base = self.PUBLIC_LOG_BASE_URL or self.BASE_URL
        return base.rstrip("/")


settings = Settings()

# Ensure directories exist
os.makedirs(settings.LOG_DIRECTORY, exist_ok=True)
os.makedirs(settings.DATA_CACHE_DIR, exist_ok=True)
