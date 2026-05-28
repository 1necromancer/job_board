import json
import logging
from typing import Any

import redis.asyncio as redis

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

_redis: redis.Redis | None = None
_disabled: bool = False

CHANNEL_NEW_APPLICATION = "applications:new"
CHANNEL_JOB_CHANGED = "jobs:changed"
JOBS_LIST_CACHE_KEY = "jobs:list:open"
JOBS_LIST_TTL = 60


def get_redis() -> redis.Redis | None:
    """Return the shared async Redis client, or None when Redis is disabled."""
    global _redis, _disabled
    if _disabled:
        return None
    if _redis is None:
        if not settings.REDIS_URL:
            logger.warning("REDIS_URL is not set — Redis features are disabled.")
            _disabled = True
            return None
        _redis = redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=False,
        )
    return _redis


async def close_redis() -> None:
    global _redis
    if _redis is not None:
        try:
            await _redis.aclose()
        except Exception:
            logger.exception("Error closing Redis")
        _redis = None


async def publish(channel: str, payload: dict[str, Any]) -> None:
    r = get_redis()
    if r is None:
        return
    try:
        await r.publish(channel, json.dumps(payload, default=str))
    except Exception:
        logger.exception("Redis publish failed (channel=%s)", channel)


async def cache_get(key: str) -> Any | None:
    r = get_redis()
    if r is None:
        return None
    try:
        raw = await r.get(key)
        return json.loads(raw) if raw else None
    except Exception:
        logger.exception("Redis cache_get failed (key=%s)", key)
        return None


async def cache_set(key: str, value: Any, ttl: int) -> None:
    r = get_redis()
    if r is None:
        return
    try:
        await r.set(key, json.dumps(value, default=str), ex=ttl)
    except Exception:
        logger.exception("Redis cache_set failed (key=%s)", key)


async def cache_invalidate(key: str) -> None:
    r = get_redis()
    if r is None:
        return
    try:
        await r.delete(key)
    except Exception:
        logger.exception("Redis cache_invalidate failed (key=%s)", key)


async def rate_limit_apply(email: str, job_id: int, window: int = 3600) -> bool:
    """Returns True if allowed, False if rate-limited. Allows when Redis is down."""
    r = get_redis()
    if r is None:
        return True
    key = f"rl:apply:{job_id}:{email.lower()}"
    try:
        if await r.exists(key):
            return False
        await r.set(key, "1", ex=window)
        return True
    except Exception:
        logger.exception("Redis rate_limit failed — allowing request")
        return True
