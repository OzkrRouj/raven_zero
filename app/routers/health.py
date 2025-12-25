import os
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from redis.asyncio import Redis

from app.config import settings
from app.core.logger import logger
from app.core.redis import get_redis
from app.models.schemas import HealthResponse
from app.services.diceware import diceware_service

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("/", response_model=HealthResponse)
async def health_check(redis: Redis = Depends(get_redis)):
    services = {
        "redis": "offline",
        "storage": "offline",
        "scheduler": "offline",
        "diceware": "offline",
    }

    try:
        if await redis.ping():
            services["redis"] = "online"
    except Exception:
        pass

    if os.access(settings.storage_path, os.W_OK):
        services["storage"] = "online"

    try:
        last_heartbeat = await redis.get("health:scheduler_heartbeat")
        if last_heartbeat:
            services["scheduler"] = "online"
    except Exception:
        pass

    try:
        stats = diceware_service.get_stats()
        if stats.get("wordlist_size") == 7776:
            services["diceware"] = "online"
    except Exception:
        pass

    critical_services = [services["redis"], services["storage"], services["diceware"]]
    is_healthy = all(s == "online" for s in critical_services)

    if is_healthy:
        logger.info("health_check_completed", status="healthy", services=services)
    else:
        logger.warning("health_check_completed", status="degraded", services=services)

    return HealthResponse(
        status="healthy" if is_healthy else "degraded",
        version="0.1.0",
        timestamp=datetime.now(timezone.utc),
        services=services,
    )
