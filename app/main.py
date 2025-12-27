from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from scalar_fastapi import get_scalar_api_reference
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


app = FastAPI(
    title="Raven Zero API",
    description="""
# Raven Zero - Ephemeral File Sharing

**Privacy by design. Files self-destruct after download or time limit.**

## Quick Start

Upload a file:
```bash
curl -F "file=@document.pdf" -F "expiry=10" -F "uses=1" https://rzapi.ozkr.dev/upload/
```

Download:
```bash
curl https://rzapi.ozkr.dev/download/apple-banana-cherry -o file.pdf
```

## Features
- 🔥 **Auto-destruction**: Files expire by time OR download count
- 🔒 **Encrypted storage**: AES-256 encryption at rest
- 🎲 **Diceware keys**: Human-readable, shareable keys
- ⚡ **No registration**: Anonymous by design
- 🚫 **Zero tracking**: No logs, no analytics, no cookies

## Limits
- **Max file size**: 1MB
- **Max expiry**: 60 minutes
- **Max downloads**: 5 uses
- **Rate limiting**: Active (per IP)

## Philosophy
> "The best way to protect data is to not have it."

Ephemeral by design, private by default, open by principle.
    """,
    version="0.1.0",
    lifespan=lifespan,
)
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


@app.get("/scalar", include_in_schema=False)
async def scalar_html():
    return get_scalar_api_reference(
        openapi_url=app.openapi_url,
        title=app.title,
    )
