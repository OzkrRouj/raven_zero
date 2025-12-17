from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from redis.asyncio import Redis

from app.config import settings
from app.core.redis import get_redis, redis_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Starting App...")
    try:
        await redis_client.ping()
        print("✅ Redis conected")

        settings.storage_path.mkdir(parents=True, exist_ok=True)
        print(f"📂 Storage directory: {settings.storage_path}")

    except Exception as e:
        print("\n❌ ERROR: Failed to initialize infrastructure.")
        print(f"Details: {e}")
        print("The application will now close.\n")
        # Forzamos la salida para que no parezca que todo está bien
        raise SystemExit(1)

    yield

    print("👋 Shutting down application...")
    await redis_client.close()
    print("🔌 Redis connection closed gracefully")


app = FastAPI(title="Raven Zero API", lifespan=lifespan)


@app.get("/health")
async def health_check(redis: Redis = Depends(get_redis)):
    is_alive = await redis.ping()
    return {"status": "OK", "redis": is_alive}
