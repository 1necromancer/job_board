from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth import (
    create_access_token,
    require_admin,
    verify_admin_password,
)
from app.db import get_db
from app.models import Application, Job
from app.redis_client import (
    CHANNEL_JOB_CHANGED,
    JOBS_LIST_CACHE_KEY,
    cache_invalidate,
    publish,
)
from app.schemas import (
    ApplicationWithJob,
    JobCreate,
    JobOut,
    JobUpdate,
    LoginIn,
    MessageOut,
    TokenOut,
)

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.post("/login", response_model=TokenOut)
async def login(payload: LoginIn):
    if not verify_admin_password(payload.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid password"
        )
    token, expires_in = create_access_token()
    return TokenOut(access_token=token, expires_in=expires_in)


@router.get("/me", response_model=MessageOut)
async def me(_: str = Depends(require_admin)):
    return MessageOut(message="admin")


@router.get("/jobs", response_model=list[JobOut])
async def list_all_jobs(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(require_admin),
):
    res = await db.execute(select(Job).order_by(Job.created_at.desc()))
    return res.scalars().all()


@router.post("/jobs", response_model=JobOut, status_code=status.HTTP_201_CREATED)
async def create_job(
    payload: JobCreate,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(require_admin),
):
    job = Job(**payload.model_dump())
    db.add(job)
    await db.commit()
    await db.refresh(job)
    await cache_invalidate(JOBS_LIST_CACHE_KEY)
    await publish(CHANNEL_JOB_CHANGED, {"action": "created", "id": job.id, "title": job.title})
    return job


@router.patch("/jobs/{job_id}", response_model=JobOut)
async def update_job(
    job_id: int,
    payload: JobUpdate,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(require_admin),
):
    job = await db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(job, k, v)
    await db.commit()
    await db.refresh(job)
    await cache_invalidate(JOBS_LIST_CACHE_KEY)
    await publish(CHANNEL_JOB_CHANGED, {"action": "updated", "id": job.id, "title": job.title})
    return job


@router.delete("/jobs/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job(
    job_id: int,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(require_admin),
):
    job = await db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    await db.delete(job)
    await db.commit()
    await cache_invalidate(JOBS_LIST_CACHE_KEY)
    await publish(CHANNEL_JOB_CHANGED, {"action": "deleted", "id": job_id})
    return None


@router.get("/applications", response_model=list[ApplicationWithJob])
async def list_applications(
    job_id: int | None = None,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(require_admin),
):
    stmt = (
        select(Application)
        .options(selectinload(Application.job))
        .order_by(Application.created_at.desc())
    )
    if job_id is not None:
        stmt = stmt.where(Application.job_id == job_id)
    res = await db.execute(stmt)
    return res.scalars().all()
