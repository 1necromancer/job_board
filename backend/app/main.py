import asyncio
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
    # Each startup step is isolated so a failing dependency never blocks
    # the app from serving /api/health (Railway healthcheck).
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables ensured")
    except Exception:
        logger.exception("Failed to create database tables on startup")

    r = get_redis()
    if r is not None:
        try:
            await asyncio.wait_for(r.ping(), timeout=5)
            logger.info("Redis connected")
        except Exception:
            logger.exception("Redis ping failed — continuing without Redis")

    try:
        await bot_runner.start()
    except Exception:
        logger.exception("Telegram bot failed to start — continuing without it")

    yield

    try:
        await bot_runner.stop()
    except Exception:
        logger.exception("Error stopping Telegram bot")
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
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(public.router)
app.include_router(admin.router)


@app.get("/", include_in_schema=False)
async def root():
    return {"name": settings.APP_NAME, "docs": "/docs"}
