import logging

from aiogram import F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from app.bot import services
from app.bot.keyboards import (
    cancel_kb,
    confirm_delete,
    job_actions,
    main_menu,
    skip_cancel_kb,
    status_kb,
)

logger = logging.getLogger(__name__)
router = Router()


class NewJob(StatesGroup):
    title = State()
    company = State()
    location = State()
    description = State()
    salary = State()
    confirm = State()


def _format_job(job: dict) -> str:
    salary = f"\n💰 {job['salary']}" if job.get("salary") else ""
    return (
        f"<b>{job['title']}</b> · <i>{job['status']}</i>\n"
        f"🏢 {job['company']} · 📍 {job['location']}{salary}\n\n"
        f"{job['description']}"
    )


# ---------- LIST -----------------------------------------------------------

@router.message(Command("jobs"))
@router.message(F.text == "📋 Jobs")
async def list_jobs(message: Message):
    try:
        jobs = await services.list_jobs()
    except Exception:
        logger.exception("Failed to fetch jobs")
        await message.answer("❌ Failed to fetch jobs.")
        return

    if not jobs:
        await message.answer("No jobs yet. Use ➕ New job to create one.")
        return

    await message.answer(f"📋 Found <b>{len(jobs)}</b> jobs:")
    for job in jobs[:20]:
        await message.answer(
            _format_job(job), reply_markup=job_actions(job["id"], job["status"])
        )


# ---------- NEW JOB FSM ----------------------------------------------------

@router.message(Command("new"))
@router.message(F.text == "➕ New job")
async def new_job_start(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(NewJob.title)
    await message.answer("Let's create a new job. What's the <b>title</b>?", reply_markup=cancel_kb())


@router.message(StateFilter(NewJob.title), F.text)
async def new_job_title(message: Message, state: FSMContext):
    if message.text and message.text.startswith("✖️"):
        await state.clear()
        await message.answer("Cancelled.", reply_markup=main_menu())
        return
    if not message.text or len(message.text) < 2:
        await message.answer("Title must be at least 2 characters. Try again:")
        return
    await state.update_data(title=message.text.strip())
    await state.set_state(NewJob.company)
    await message.answer("Great. <b>Company</b>?")


@router.message(StateFilter(NewJob.company), F.text)
async def new_job_company(message: Message, state: FSMContext):
    if message.text and message.text.startswith("✖️"):
        await state.clear()
        await message.answer("Cancelled.", reply_markup=main_menu())
        return
    await state.update_data(company=(message.text or "").strip())
    await state.set_state(NewJob.location)
    await message.answer("<b>Location</b>? (e.g. Remote, Berlin, NYC)")


@router.message(StateFilter(NewJob.location), F.text)
async def new_job_location(message: Message, state: FSMContext):
    if message.text and message.text.startswith("✖️"):
        await state.clear()
        await message.answer("Cancelled.", reply_markup=main_menu())
        return
    await state.update_data(location=(message.text or "").strip())
    await state.set_state(NewJob.description)
    await message.answer("Now the <b>description</b> (min 10 chars):")


@router.message(StateFilter(NewJob.description), F.text)
async def new_job_description(message: Message, state: FSMContext):
    if message.text and message.text.startswith("✖️"):
        await state.clear()
        await message.answer("Cancelled.", reply_markup=main_menu())
        return
    if not message.text or len(message.text) < 10:
        await message.answer("Description must be at least 10 characters. Try again:")
        return
    await state.update_data(description=message.text.strip())
    await state.set_state(NewJob.salary)
    await message.answer(
        "<b>Salary</b>? (optional, e.g. $80k–$110k). Tap Skip if N/A.",
        reply_markup=skip_cancel_kb(),
    )


@router.message(StateFilter(NewJob.salary), F.text)
async def new_job_salary(message: Message, state: FSMContext):
    text = (message.text or "").strip()
    if text.startswith("✖️"):
        await state.clear()
        await message.answer("Cancelled.", reply_markup=main_menu())
        return
    salary = None if text.startswith("⏭") or not text else text
    await state.update_data(salary=salary)
    await state.set_state(NewJob.confirm)

    data = await state.get_data()
    summary = (
        "<b>Please confirm the new job:</b>\n\n"
        f"Title: {data['title']}\n"
        f"Company: {data['company']}\n"
        f"Location: {data['location']}\n"
        f"Salary: {data.get('salary') or '—'}\n\n"
        f"<b>Description:</b>\n{data['description']}\n\n"
        "Reply <b>open</b> to publish, <b>closed</b> to save as draft, or /cancel."
    )
    await message.answer(summary, reply_markup=status_kb())


@router.message(StateFilter(NewJob.confirm), F.text)
async def new_job_confirm(message: Message, state: FSMContext):
    text = (message.text or "").strip().lower()
    if text not in ("open", "closed"):
        await message.answer("Please reply <b>open</b> or <b>closed</b>.")
        return
    data = await state.get_data()
    payload = {
        "title": data["title"],
        "company": data["company"],
        "location": data["location"],
        "description": data["description"],
        "salary": data.get("salary"),
        "status": text,
    }
    try:
        job = await services.create_job(payload)
    except Exception:
        logger.exception("Failed to create job")
        await state.clear()
        await message.answer("❌ Failed to create job.", reply_markup=main_menu())
        return

    await state.clear()
    await message.answer(
        f"✅ Job created (id <code>{job['id']}</code>, status <b>{job['status']}</b>).",
        reply_markup=main_menu(),
    )
    await message.answer(_format_job(job), reply_markup=job_actions(job["id"], job["status"]))


# ---------- INLINE ACTIONS -------------------------------------------------

@router.callback_query(F.data.startswith("job:status:"))
async def cb_toggle_status(cb: CallbackQuery):
    if not cb.data:
        return
    _, _, job_id, target = cb.data.split(":")
    try:
        job = await services.update_job(int(job_id), {"status": target})
    except Exception:
        logger.exception("Failed to toggle status")
        await cb.answer("Failed", show_alert=True)
        return
    if not job:
        await cb.answer("Job not found", show_alert=True)
        return
    await cb.answer(f"Status: {job['status']}")
    if cb.message:
        await cb.message.edit_text(
            _format_job(job), reply_markup=job_actions(job["id"], job["status"])
        )


@router.callback_query(F.data.startswith("job:apps:"))
async def cb_view_apps(cb: CallbackQuery):
    if not cb.data or not cb.message:
        return
    job_id = int(cb.data.split(":")[2])
    try:
        apps = await services.list_applications(job_id)
    except Exception:
        logger.exception("Failed to fetch applications")
        await cb.answer("Failed", show_alert=True)
        return
    await cb.answer()
    if not apps:
        await cb.message.answer("No applications yet for this job.")
        return
    await cb.message.answer(f"📬 <b>{len(apps)}</b> application(s):")
    for a in apps[:20]:
        cover = f"\n\n{a['cover_letter']}" if a.get("cover_letter") else ""
        await cb.message.answer(
            f"<b>{a['full_name']}</b>\n"
            f"✉️ {a['email']}\n"
            f"🕒 {a['created_at']}{cover}"
        )


@router.callback_query(F.data.startswith("job:delete:confirm:"))
async def cb_delete_confirm(cb: CallbackQuery):
    if not cb.data:
        return
    job_id = int(cb.data.split(":")[3])
    try:
        ok = await services.delete_job(job_id)
    except Exception:
        logger.exception("Failed to delete job")
        await cb.answer("Failed", show_alert=True)
        return
    if not ok:
        await cb.answer("Job not found", show_alert=True)
        return
    await cb.answer("Deleted")
    if cb.message:
        await cb.message.edit_text(f"🗑 Job <code>{job_id}</code> deleted.")


@router.callback_query(F.data == "job:delete:cancel")
async def cb_delete_cancel(cb: CallbackQuery):
    await cb.answer("Cancelled")
    if cb.message:
        await cb.message.edit_reply_markup(reply_markup=None)


@router.callback_query(F.data.startswith("job:delete:"))
async def cb_delete_ask(cb: CallbackQuery):
    if not cb.data:
        return
    job_id = int(cb.data.split(":")[2])
    await cb.answer()
    if cb.message:
        await cb.message.answer(
            f"Delete job <code>{job_id}</code>? This cannot be undone.",
            reply_markup=confirm_delete(job_id),
        )
