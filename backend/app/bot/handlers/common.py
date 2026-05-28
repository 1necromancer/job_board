from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.bot.keyboards import main_menu

router = Router()


HELP_TEXT = (
    "<b>Job Board admin bot</b>\n\n"
    "• 📋 <b>Jobs</b> — list & manage openings\n"
    "• ➕ <b>New job</b> — create a new opening (guided)\n"
    "• 📬 <b>Applications</b> — see latest applicants\n"
    "• /cancel — abort current action\n\n"
    "You'll also receive a push here every time someone applies."
)


@router.message(CommandStart())
async def start(message: Message):
    name = message.from_user.first_name if message.from_user else "admin"
    await message.answer(
        f"👋 Hi {name}! You're connected to the Job Board.\n\n" + HELP_TEXT,
        reply_markup=main_menu(),
    )


@router.message(Command("help"))
@router.message(F.text.startswith("ℹ️"))
async def help_(message: Message):
    await message.answer(HELP_TEXT, reply_markup=main_menu())


@router.message(Command("cancel"))
@router.message(F.text.startswith("✖️ Cancel"))
async def cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Okay, cancelled.", reply_markup=main_menu())
