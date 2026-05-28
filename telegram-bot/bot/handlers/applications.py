import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.api_client import backend

logger = logging.getLogger(__name__)
router = Router()


@router.message(Command("applications"))
@router.message(F.text == "📬 Applications")
async def list_applications(message: Message):
    try:
        apps = await backend.list_applications()
    except Exception:
        logger.exception("Failed to fetch applications")
        await message.answer("❌ Failed to fetch applications from the backend.")
        return

    if not apps:
        await message.answer("No applications yet.")
        return

    await message.answer(f"📬 Latest <b>{min(len(apps), 20)}</b> of {len(apps)} applications:")
    for a in apps[:20]:
        cover = f"\n\n{a['cover_letter']}" if a.get("cover_letter") else ""
        await message.answer(
            f"<b>{a['full_name']}</b> → <i>{a['job']['title']}</i>\n"
            f"🏢 {a['job']['company']}\n"
            f"✉️ {a['email']}\n"
            f"🕒 {a['created_at']}{cover}"
        )
