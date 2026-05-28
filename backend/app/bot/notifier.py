import asyncio
import json
import logging

import redis.asyncio as redis
from aiogram import Bot

from app.config import get_settings
from app.redis_client import CHANNEL_NEW_APPLICATION

logger = logging.getLogger(__name__)


async def listen_new_applications(bot: Bot) -> None:
    """Subscribe to Redis and forward new application events to all admins."""
    s = get_settings()
    if not s.REDIS_URL:
        logger.warning("REDIS_URL is not set — bot notifications disabled.")
        return
    while True:
        try:
            client = redis.from_url(
                s.REDIS_URL,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=None,  # pub/sub keeps the socket open indefinitely
            )
            pubsub = client.pubsub()
            await pubsub.subscribe(CHANNEL_NEW_APPLICATION)
            logger.info("Bot subscribed to %s", CHANNEL_NEW_APPLICATION)

            async for msg in pubsub.listen():
                if msg.get("type") != "message":
                    continue
                try:
                    data = json.loads(msg["data"])
                except Exception:
                    logger.exception("Bad pub/sub payload")
                    continue
                text = (
                    "🔔 <b>New application</b>\n"
                    f"<b>{data.get('full_name')}</b> applied to "
                    f"<i>{data.get('job_title')}</i> @ {data.get('company')}\n"
                    f"✉️ {data.get('email')}"
                )
                for admin_id in s.ADMIN_TG_IDS:
                    try:
                        await bot.send_message(admin_id, text)
                    except Exception:
                        logger.exception("Failed to notify admin %s", admin_id)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Pub/sub loop crashed, reconnecting in 5s")
            await asyncio.sleep(5)
