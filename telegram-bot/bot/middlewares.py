from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from bot.config import get_settings


class WhitelistMiddleware(BaseMiddleware):
    """Drop messages from anyone outside ADMIN_TG_IDS."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        admins = set(get_settings().ADMIN_TG_IDS)
        user_id: int | None = None
        if isinstance(event, Message) and event.from_user:
            user_id = event.from_user.id
        elif isinstance(event, CallbackQuery) and event.from_user:
            user_id = event.from_user.id

        if user_id is None or user_id not in admins:
            if isinstance(event, Message):
                await event.answer(
                    "🚫 Access denied. Your Telegram ID is not in the admin whitelist."
                )
            elif isinstance(event, CallbackQuery):
                await event.answer("Access denied", show_alert=True)
            return None
        return await handler(event, data)
