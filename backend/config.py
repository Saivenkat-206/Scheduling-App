from pydantic_settings import BaseSettings
from typing import List
from pathlib import Path


class Settings(BaseSettings):
    DEBUG: bool = False
    ALLOWED_ORIGINS: List[str] = []
    MAX_UPLOAD_SIZE: int = 5 * 1024 * 1024  # bytes, default 5 MB
    ALLOW_WRITE: bool = True
    LOG_FILE: str = "app.log"

    class Config:
        env_file = str(Path(__file__).resolve().parents[1] / ".env")


settings = Settings()
