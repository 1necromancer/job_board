import json
from typing import Any

import redis.asyncio as redis

from app.config import get_settings

settings = get_settings()

_redis: redis.Redis | None = None

CHANNEL_NEW_APPLICATION = "applications:new"
CHANNEL_JOB_CHANGED = "jobs:changed"
JOBS_LIST_CACHE_KEY = "jobs:list:open"
JOBS_LIST_TTL = 60


def get_redis() -> redis.Redis:
    global _redis
    if _redis is None:
        _redis = redis.from_url(
            settings.REDIS_URL, encoding="utf-8", decode_responses=True
        )
    return _redis


async def close_redis() -> None:
    global _redis
    if _redis is not None:
        await _redis.aclose()
        _redis = None


async def publish(channel: str, payload: dict[str, Any]) -> None:
    r = get_redis()
    await r.publish(channel, json.dumps(payload, default=str))


async def cache_get(key: str) -> Any | None:
    r = get_redis()
    raw = await r.get(key)
    return json.loads(raw) if raw else None


async def cache_set(key: str, value: Any, ttl: int) -> None:
    r = get_redis()
    await r.set(key, json.dumps(value, default=str), ex=ttl)


async def cache_invalidate(key: str) -> None:
    r = get_redis()
    await r.delete(key)


async def rate_limit_apply(email: str, job_id: int, window: int = 3600) -> bool:
    """Returns True if allowed, False if rate-limited."""
    r = get_redis()
    key = f"rl:apply:{job_id}:{email.lower()}"
    if await r.exists(key):
        return False
    await r.set(key, "1", ex=window)
    return True
