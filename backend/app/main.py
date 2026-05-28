import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.bot.runner import bot_runner
from app.config import get_settings
from app.db import Base, engine
from app.redis_client import close_redis, get_redis
from app.routers import admin, public

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Create tables on startup. Alembic migrations are also provided for production.
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # Warm Redis client + ping.
    try:
        await get_redis().ping()
        logger.info("Redis connected")
    except Exception:
        logger.exception("Redis ping failed")
    # Telegram bot runs in-process as a background task.
    await bot_runner.start()
    yield
    await bot_runner.stop()
    await close_redis()
    await engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(public.router)
app.include_router(admin.router)


@app.get("/", include_in_schema=False)
async def root():
    return {"name": settings.APP_NAME, "docs": "/docs"}
