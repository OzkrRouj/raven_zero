from fastapi import APIRouter, Depends, HTTPException, Request
from redis.asyncio import Redis

from app.config import settings
from app.core.logger import logger
from app.core.rate_limiting import get_client_ip
from app.core.redis import get_redis
from app.models.schemas import PreviewResponse
from app.services.cache import cache_service

router = APIRouter(prefix="/preview", tags=["Preview"])


@router.get("/{key}", response_model=PreviewResponse)
async def preview_upload(key: str, request: Request, redis: Redis = Depends(get_redis)):
    client_ip = get_client_ip(request)
    block_key = f"block:preview:{client_ip}"
    fail_key = f"fails:preview:{client_ip}"

    if await redis.get(block_key):
        logger.warning(
            "blocked_ip_attempted_preview", extra={"ip": client_ip, "key": key}
        )
        raise HTTPException(
            status_code=429, detail="Demasiados intentos fallidos. Inténtalo más tarde."
        )

    if not await cache_service.exists(redis, key):
        fails = await redis.incr(fail_key)
        await redis.expire(fail_key, 600)

        if fails >= settings.download_fail_limit:
            await redis.setex(block_key, settings.download_block_window, "1")
            logger.error("ip_blocked_brute_force_preview", extra={"ip": client_ip})

        logger.warning(
            "preview_not_found_failed_attempt", extra={"ip": client_ip, "key": key}
        )
        raise HTTPException(status_code=404, detail="Upload not found or link expired")

    was_first_time = await cache_service.mark_as_previewed_atomic(redis, key)

    if not was_first_time:
        logger.warning("preview_already_accessed")
        raise HTTPException(
            status_code=404,
            detail="""
            This file preview has already been accessed
            and is no longer available for security reasons.
            """,
        )

    metadata = await cache_service.get_upload_metadata(redis, key)
    ttl = await cache_service.get_ttl(redis, key)

    logger.info("preview_requested")

    base_url = str(request.base_url).rstrip("/")
    download_url = f"{base_url}/download/{key}"

    return PreviewResponse(
        key=key,
        filename=metadata["filename"],
        size=int(metadata["size"]),
        mime_type=metadata["mime_type"],
        expiry=metadata["expiry_at"],
        uses=metadata["uses"],
        minutes_left=max(0, ttl // 60),
        download_url=download_url,
        curl_example=f"curl -O {download_url}",
        created_at=metadata["created_at"],
        sha256=metadata.get("sha256", "unknown"),
    )
