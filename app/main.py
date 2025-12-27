from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings
from app.core.logger import logger, setup_logging
from app.core.logging_middleware import logging_middleware
from app.core.rate_limiting import init_rate_limiting
from app.core.redis import redis_client
from app.core.security_headers import SecurityHeadersMiddleware
from app.core.uptime import uptime_tracker
from app.routers import download, health, preview, status, upload
from app.services.scheduler import shutdown_scheduler, start_scheduler

setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("app_starting")
    try:
        await redis_client.ping()
        logger.info("redis_connected")

        uptime_tracker.start()
        logger.info("uptime_tracker_started")

        settings.storage_path.mkdir(parents=True, exist_ok=True)
        logger.info("storage_directory_initialized", path=str(settings.storage_path))
        if hasattr(settings, "temp_path"):
            settings.temp_path.mkdir(parents=True, exist_ok=True)

        start_scheduler()
        logger.info("scheduler_started_successfully")

    except Exception as e:
        logger.critical("infrastructure_initialization_failed", error=str(e))
        raise SystemExit(1)

    try:
        yield
    finally:
        logger.info("application_shutdown_started")
        shutdown_scheduler()
        await redis_client.close()
        logger.info("redis_connection_closed")


app = FastAPI(title="Raven Zero API", lifespan=lifespan)

init_rate_limiting(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Accept"],
)

app.add_middleware(BaseHTTPMiddleware, dispatch=logging_middleware)
app.add_middleware(SecurityHeadersMiddleware)

app.include_router(upload.router)
app.include_router(preview.router)
app.include_router(download.router)
app.include_router(health.router)
app.include_router(status.router)
