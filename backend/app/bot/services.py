"""Direct DB service layer for the in-process Telegram bot.

The bot runs inside the FastAPI worker, so we skip HTTP and talk to Postgres
directly via the same SQLAlchemy session factory the API uses.
"""
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db import SessionLocal
from app.models import Application, Job, JobStatus
from app.redis_client import (
    CHANNEL_JOB_CHANGED,
    JOBS_LIST_CACHE_KEY,
    cache_invalidate,
    publish,
)


def _job_to_dict(job: Job) -> dict[str, Any]:
    return {
        "id": job.id,
        "title": job.title,
        "company": job.company,
        "location": job.location,
        "description": job.description,
        "salary": job.salary,
        "status": job.status.value if isinstance(job.status, JobStatus) else job.status,
        "created_at": job.created_at.isoformat(),
        "updated_at": job.updated_at.isoformat(),
    }


def _application_to_dict(app: Application) -> dict[str, Any]:
    return {
        "id": app.id,
        "job_id": app.job_id,
        "full_name": app.full_name,
        "email": app.email,
        "cover_letter": app.cover_letter,
        "created_at": app.created_at.isoformat(),
        "job": _job_to_dict(app.job),
    }


async def list_jobs() -> list[dict[str, Any]]:
    async with SessionLocal() as db:
        res = await db.execute(select(Job).order_by(Job.created_at.desc()))
        return [_job_to_dict(j) for j in res.scalars().all()]


async def create_job(payload: dict[str, Any]) -> dict[str, Any]:
    async with SessionLocal() as db:
        job = Job(
            title=payload["title"],
            company=payload["company"],
            location=payload["location"],
            description=payload["description"],
            salary=payload.get("salary"),
            status=JobStatus(payload.get("status", "open")),
        )
        db.add(job)
        await db.commit()
        await db.refresh(job)
        await cache_invalidate(JOBS_LIST_CACHE_KEY)
        await publish(
            CHANNEL_JOB_CHANGED,
            {"action": "created", "id": job.id, "title": job.title},
        )
        return _job_to_dict(job)


async def update_job(job_id: int, payload: dict[str, Any]) -> dict[str, Any] | None:
    async with SessionLocal() as db:
        job = await db.get(Job, job_id)
        if not job:
            return None
        for k, v in payload.items():
            if k == "status" and isinstance(v, str):
                v = JobStatus(v)
            setattr(job, k, v)
        await db.commit()
        await db.refresh(job)
        await cache_invalidate(JOBS_LIST_CACHE_KEY)
        await publish(
            CHANNEL_JOB_CHANGED,
            {"action": "updated", "id": job.id, "title": job.title},
        )
        return _job_to_dict(job)


async def delete_job(job_id: int) -> bool:
    async with SessionLocal() as db:
        job = await db.get(Job, job_id)
        if not job:
            return False
        await db.delete(job)
        await db.commit()
        await cache_invalidate(JOBS_LIST_CACHE_KEY)
        await publish(CHANNEL_JOB_CHANGED, {"action": "deleted", "id": job_id})
        return True


async def list_applications(job_id: int | None = None) -> list[dict[str, Any]]:
    async with SessionLocal() as db:
        stmt = (
            select(Application)
            .options(selectinload(Application.job))
            .order_by(Application.created_at.desc())
        )
        if job_id is not None:
            stmt = stmt.where(Application.job_id == job_id)
        res = await db.execute(stmt)
        return [_application_to_dict(a) for a in res.scalars().all()]
