from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)


def main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📋 Jobs"), KeyboardButton(text="➕ New job")],
            [KeyboardButton(text="📬 Applications"), KeyboardButton(text="ℹ️ Help")],
        ],
        resize_keyboard=True,
        is_persistent=True,
    )


def cancel_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="✖️ Cancel")]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def skip_cancel_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="⏭ Skip"), KeyboardButton(text="✖️ Cancel")]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def status_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="open"), KeyboardButton(text="closed")]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def job_actions(job_id: int, status: str) -> InlineKeyboardMarkup:
    toggle_label = "🔒 Close" if status == "open" else "🔓 Reopen"
    toggle_target = "closed" if status == "open" else "open"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=toggle_label, callback_data=f"job:status:{job_id}:{toggle_target}"
                ),
                InlineKeyboardButton(
                    text="📬 Applicants", callback_data=f"job:apps:{job_id}"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🗑 Delete", callback_data=f"job:delete:{job_id}"
                ),
            ],
        ]
    )


def confirm_delete(job_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Yes, delete", callback_data=f"job:delete:confirm:{job_id}"
                ),
                InlineKeyboardButton(text="✖️ Cancel", callback_data="job:delete:cancel"),
            ]
        ]
    )
