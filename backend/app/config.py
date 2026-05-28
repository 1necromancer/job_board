from functools import lru_cache
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Railway injects these automatically when you attach the plugins.
    DATABASE_URL: str = Field(..., description="PostgreSQL connection string")
    REDIS_URL: str | None = Field(
        default=None,
        description="Redis connection string. If empty, cache/pub-sub/rate-limit are no-op.",
    )

    # Auth
    ADMIN_PASSWORD: str = Field(..., description="Plain admin password (hashed in memory at startup)")
    JWT_SECRET: str = Field(..., min_length=16)
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRES_MINUTES: int = 60 * 12  # 12h

    # Email
    RESEND_API_KEY: str | None = None
    RESEND_FROM: str = "Job Board <onboarding@resend.dev>"

    # CORS — stored as a raw string to avoid pydantic-settings JSON decoding.
    # Use a comma-separated list, e.g. "https://a.com,https://b.com" or "*".
    CORS_ORIGINS: str = "*"

    # Telegram bot (optional — bot only starts when BOT_TOKEN is set).
    # ADMIN_TG_IDS is a raw comma-separated string for the same reason as CORS.
    BOT_TOKEN: str | None = None
    ADMIN_TG_IDS_RAW: str = Field(default="", alias="ADMIN_TG_IDS")

    # Misc
    APP_NAME: str = "Job Board API"
    DEBUG: bool = False

    @field_validator("DATABASE_URL")
    @classmethod
    def normalize_db_url(cls, v: str) -> str:
        # SQLAlchemy async needs postgresql+asyncpg:// prefix
        if v.startswith("postgres://"):
            v = v.replace("postgres://", "postgresql://", 1)
        if v.startswith("postgresql://") and "+asyncpg" not in v:
            v = v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v

    @property
    def cors_origins_list(self) -> List[str]:
        raw = (self.CORS_ORIGINS or "").strip()
        if not raw or raw == "*":
            return ["*"]
        return [o.strip() for o in raw.split(",") if o.strip()]

    @property
    def ADMIN_TG_IDS(self) -> List[int]:
        raw = (self.ADMIN_TG_IDS_RAW or "").strip()
        if not raw:
            return []
        out: List[int] = []
        for part in raw.split(","):
            part = part.strip()
            if not part:
                continue
            try:
                out.append(int(part))
            except ValueError:
                continue
        return out


@lru_cache
def get_settings() -> Settings:
    return Settings()
