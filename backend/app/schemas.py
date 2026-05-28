from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models import JobStatus


class JobBase(BaseModel):
    title: str = Field(..., min_length=2, max_length=200)
    company: str = Field(..., min_length=1, max_length=120)
    location: str = Field(..., min_length=1, max_length=120)
    description: str = Field(..., min_length=10)
    salary: str | None = Field(None, max_length=120)


class JobCreate(JobBase):
    status: JobStatus = JobStatus.open


class JobUpdate(BaseModel):
    title: str | None = Field(None, min_length=2, max_length=200)
    company: str | None = Field(None, min_length=1, max_length=120)
    location: str | None = Field(None, min_length=1, max_length=120)
    description: str | None = Field(None, min_length=10)
    salary: str | None = Field(None, max_length=120)
    status: JobStatus | None = None


class JobOut(JobBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: JobStatus
    created_at: datetime
    updated_at: datetime


class ApplicationCreate(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=120)
    email: EmailStr
    cover_letter: str | None = Field(None, max_length=5000)


class ApplicationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    job_id: int
    full_name: str
    email: EmailStr
    cover_letter: str | None
    created_at: datetime


class ApplicationWithJob(ApplicationOut):
    job: JobOut


class LoginIn(BaseModel):
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class MessageOut(BaseModel):
    message: str
