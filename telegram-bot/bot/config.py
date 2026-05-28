from functools import lru_cache
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    BOT_TOKEN: str = Field(..., description="Telegram bot token from @BotFather")
    ADMIN_TG_IDS: List[int] = Field(default_factory=list)

    BACKEND_URL: str = Field(..., description="Public backend URL, e.g. https://api-xxx.up.railway.app")
    ADMIN_PASSWORD: str = Field(..., description="Same admin password as backend")

    REDIS_URL: str = Field(..., description="Same Redis as backend (for pub/sub)")

    @field_validator("ADMIN_TG_IDS", mode="before")
    @classmethod
    def split_ids(cls, v):
        if isinstance(v, str):
            return [int(x.strip()) for x in v.split(",") if x.strip()]
        return v


@lru_cache
def get_settings() -> Settings:
    return Settings()
