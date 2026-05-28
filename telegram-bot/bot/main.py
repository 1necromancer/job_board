import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from bot.api_client import backend
from bot.config import get_settings
from bot.handlers import applications, common, jobs
from bot.middlewares import WhitelistMiddleware
from bot.notifier import listen_new_applications

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)


async def main() -> None:
    settings = get_settings()
    if not settings.ADMIN_TG_IDS:
        logger.warning("ADMIN_TG_IDS is empty — bot will reject every user.")

    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())

    whitelist = WhitelistMiddleware()
    dp.message.middleware(whitelist)
    dp.callback_query.middleware(whitelist)

    dp.include_router(common.router)
    dp.include_router(jobs.router)
    dp.include_router(applications.router)

    asyncio.create_task(listen_new_applications(bot))

    try:
        logger.info("Bot starting (long-polling)")
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await backend.close()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
