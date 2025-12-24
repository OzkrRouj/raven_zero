from fastapi import APIRouter, Depends, HTTPException, Request
from redis.asyncio import Redis

from app.core.redis import get_redis
from app.models.schemas import PreviewResponse
from app.services.cache import cache_service

router = APIRouter(prefix="/preview", tags=["Preview"])


@router.get("/{key}", response_model=PreviewResponse)
async def preview_upload(key: str, request: Request, redis: Redis = Depends(get_redis)):
    if not await cache_service.exists(redis, key):
        raise HTTPException(status_code=404, detail="Upload not found or expired")

    was_first_time = await cache_service.mark_as_previewed_atomic(redis, key)

    if not was_first_time:
        raise HTTPException(
            status_code=404,
            detail="""
            This file preview has already been accessed 
            and is no longer available for security reasons.
            """,
        )

    metadata = await cache_service.get_upload_metadata(redis, key)
    ttl = await cache_service.get_ttl(redis, key)

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
    )
