from functools import lru_cache
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _csv_to_int_list(v):
    if isinstance(v, str):
        return [int(x.strip()) for x in v.split(",") if x.strip()]
    return v


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Railway injects these automatically when you attach the plugins.
    # DATABASE_URL example: postgresql://user:pass@host:port/db
    # REDIS_URL example: redis://default:pass@host:port
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

    # CORS
    CORS_ORIGINS: List[str] = ["*"]

    # Telegram bot (optional — bot only starts when BOT_TOKEN is set)
    BOT_TOKEN: str | None = None
    ADMIN_TG_IDS: List[int] = Field(default_factory=list)

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

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def split_origins(cls, v):
        if isinstance(v, str):
            return [o.strip() for o in v.split(",") if o.strip()]
        return v

    @field_validator("ADMIN_TG_IDS", mode="before")
    @classmethod
    def split_tg_ids(cls, v):
        return _csv_to_int_list(v)


@lru_cache
def get_settings() -> Settings:
    return Settings()
