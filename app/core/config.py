"""
FocuseMate Backend - Core Configuration
"""
from __future__ import annotations

import json
from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # ── Application ──────────────────────────────────────────────
    APP_NAME: str = "FocuseMate"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── Database ─────────────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://mydatabase_cpj0_user:suPpDNHiKk5i9LHVJW3whDHFFhM5hUTG@dpg-d77vqa6uk2gs73b195tg-a.oregon-postgres.render.com/mydatabase_cpj0"
    DATABASE_ECHO: bool = False

    # ── CORS ─────────────────────────────────────────────────────
    CORS_ORIGINS: str = '["http://localhost:3000","http://localhost:8081"]'

    # ── Rate Limiting ────────────────────────────────────────────
    RATE_LIMIT_PER_MINUTE: int = 60

    # ── Logging ──────────────────────────────────────────────────
    LOG_LEVEL: str = "INFO"

    @property
    def cors_origins_list(self) -> List[str]:
        try:
            return json.loads(self.CORS_ORIGINS)
        except (json.JSONDecodeError, TypeError):
            return ["*"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = Settings()
