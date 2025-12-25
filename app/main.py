from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import settings
from app.core.redis import redis_client
from app.core.security_headers import SecurityHeadersMiddleware
from app.routers import download, health, preview, upload
from app.services.scheduler import shutdown_scheduler, start_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Starting App...")
    try:
        await redis_client.ping()
        print("✅ Redis connected")

        settings.storage_path.mkdir(parents=True, exist_ok=True)
        print(f"📂 Storage directory: {settings.storage_path}")
        if hasattr(settings, "temp_path"):
            settings.temp_path.mkdir(parents=True, exist_ok=True)

        start_scheduler()
        print("✅ Scheduler started successfully")

    except Exception as e:
        print("\n❌ ERROR: Failed to initialize infrastructure.")
        print(f"Details: {e}")
        print("The application will now close.\n")
        raise SystemExit(1)

    yield

    print("👋 Shutting down application...")

    shutdown_scheduler()

    await redis_client.close()
    print("🔌 Redis connection closed gracefully")


app = FastAPI(title="Raven Zero API", lifespan=lifespan)

app.add_middleware(SecurityHeadersMiddleware)

app.include_router(upload.router)
app.include_router(preview.router)
app.include_router(download.router)
app.include_router(health.router)
