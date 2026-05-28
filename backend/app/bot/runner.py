import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from app.bot.handlers import applications, common, jobs
from app.bot.middlewares import WhitelistMiddleware
from app.bot.notifier import listen_new_applications
from app.config import get_settings

logger = logging.getLogger(__name__)


class BotRunner:
    """Runs aiogram polling + Redis pub/sub listener as background tasks."""

    def __init__(self) -> None:
        self._bot: Bot | None = None
        self._dp: Dispatcher | None = None
        self._polling_task: asyncio.Task | None = None
        self._notifier_task: asyncio.Task | None = None

    async def start(self) -> None:
        s = get_settings()
        if not s.BOT_TOKEN:
            logger.info("BOT_TOKEN not set, Telegram bot disabled.")
            return
        if not s.ADMIN_TG_IDS:
            logger.warning("ADMIN_TG_IDS is empty — bot will reject every user.")

        bot = Bot(
            token=s.BOT_TOKEN,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML),
        )
        dp = Dispatcher(storage=MemoryStorage())

        whitelist = WhitelistMiddleware()
        dp.message.middleware(whitelist)
        dp.callback_query.middleware(whitelist)

        dp.include_router(common.router)
        dp.include_router(jobs.router)
        dp.include_router(applications.router)

        self._bot = bot
        self._dp = dp
        self._polling_task = asyncio.create_task(
            dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types()),
            name="tg-polling",
        )
        self._notifier_task = asyncio.create_task(
            listen_new_applications(bot), name="tg-notifier"
        )
        logger.info("Telegram bot started (polling + notifier)")

    async def stop(self) -> None:
        for task in (self._notifier_task, self._polling_task):
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except (asyncio.CancelledError, Exception):
                    pass
        if self._dp is not None:
            try:
                await self._dp.stop_polling()
            except Exception:
                pass
        if self._bot is not None:
            try:
                await self._bot.session.close()
            except Exception:
                pass
        logger.info("Telegram bot stopped")


bot_runner = BotRunner()
