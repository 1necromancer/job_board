from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models import Application, Job, JobStatus
from app.redis_client import (
    CHANNEL_NEW_APPLICATION,
    JOBS_LIST_CACHE_KEY,
    JOBS_LIST_TTL,
    cache_get,
    cache_set,
    publish,
    rate_limit_apply,
)
from app.schemas import ApplicationCreate, ApplicationOut, JobOut, MessageOut
from app.services.email import send_application_confirmation

router = APIRouter(prefix="/api", tags=["public"])


@router.get("/jobs", response_model=list[JobOut])
async def list_open_jobs(db: AsyncSession = Depends(get_db)):
    cached = await cache_get(JOBS_LIST_CACHE_KEY)
    if cached is not None:
        return cached

    res = await db.execute(
        select(Job).where(Job.status == JobStatus.open).order_by(Job.created_at.desc())
    )
    jobs = res.scalars().all()
    payload = [JobOut.model_validate(j).model_dump(mode="json") for j in jobs]
    await cache_set(JOBS_LIST_CACHE_KEY, payload, JOBS_LIST_TTL)
    return payload


@router.get("/jobs/{job_id}", response_model=JobOut)
async def get_job(job_id: int, db: AsyncSession = Depends(get_db)):
    job = await db.get(Job, job_id)
    if not job or job.status != JobStatus.open:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.post(
    "/jobs/{job_id}/apply",
    response_model=ApplicationOut,
    status_code=status.HTTP_201_CREATED,
)
async def apply_to_job(
    job_id: int,
    payload: ApplicationCreate,
    background: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    job = await db.get(Job, job_id)
    if not job or job.status != JobStatus.open:
        raise HTTPException(status_code=404, detail="Job not found or closed")

    allowed = await rate_limit_apply(payload.email, job_id)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="You have already applied to this job recently. Try again later.",
        )

    application = Application(
        job_id=job_id,
        full_name=payload.full_name,
        email=payload.email,
        cover_letter=payload.cover_letter,
    )
    db.add(application)
    await db.commit()
    await db.refresh(application)

    # Notify Telegram bot via Redis pub/sub (decoupled).
    await publish(
        CHANNEL_NEW_APPLICATION,
        {
            "application_id": application.id,
            "job_id": job.id,
            "job_title": job.title,
            "company": job.company,
            "full_name": application.full_name,
            "email": application.email,
            "created_at": application.created_at.isoformat(),
        },
    )

    # Send confirmation email out-of-band.
    background.add_task(
        send_application_confirmation,
        application.email,
        application.full_name,
        job.title,
        job.company,
    )

    return application


@router.get("/health", response_model=MessageOut, include_in_schema=False)
async def health():
    return MessageOut(message="ok")
