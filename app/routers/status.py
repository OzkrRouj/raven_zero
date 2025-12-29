from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from redis.asyncio import Redis

from app.config import settings
from app.core.logger import logger
from app.core.rate_limiting import get_client_ip
from app.core.redis import get_redis
from app.models.schemas import ErrorResponse, StatusResponse

router = APIRouter(prefix="/status", tags=["Status"])


@router.get(
    "/{key}", response_model=StatusResponse, responses={404: {"model": ErrorResponse}}
)
async def get_file_status(
    key: str, request: Request, redis: Redis = Depends(get_redis)
):
    client_ip = get_client_ip(request)
    block_key = f"block:status:{client_ip}"
    fail_key = f"fails:status:{client_ip}"

    if await redis.get(block_key):
        ttl = await redis.ttl(block_key)
        logger.warning(
            "blocked_ip_attempted_status",
            extra={"ip": client_ip, "key": key, "ttl": ttl},
        )
        raise HTTPException(
            status_code=429,
            detail={
                "error": "Too many failed attempts. Temporarily blocked.",
                "retry_after_seconds": ttl,
            },
        )

    data = await redis.hgetall(f"upload:{key}")
    uses = await redis.get(f"upload:{key}:uses")

    if not data:
        fails = await redis.incr(fail_key)
        await redis.expire(fail_key, 600)

        if fails >= settings.download_fail_limit:
            await redis.setex(block_key, settings.download_block_window, "1")
            logger.error("ip_blocked_brute_force_status", extra={"ip": client_ip})

        logger.info("status_check_not_found", extra={"key": key, "ip": client_ip})
        return StatusResponse(
            key=key, status="expired_or_burned", remaining_uses=0, is_accessible=False
        )

    uses = int(uses) if uses else 0
    expiry_str = data.get("expiry_at")

    if not expiry_str:
        logger.warning("missing_expiry_field", extra={"key": key})
        return StatusResponse(
            key=key, status="expired_or_burned", remaining_uses=0, is_accessible=False
        )

    expiry = datetime.fromisoformat(expiry_str)
    now = datetime.now(timezone.utc)

    # Determinar el estado lógico
    status = "active"
    is_accessible = True

    if now > expiry:
        status = "expired"
        is_accessible = False
    elif uses <= 0:
        status = "burned"
        is_accessible = False

    logger.info("status_check_success", extra={"key": key, "status": status})

    return StatusResponse(
        key=key,
        status=status,
        remaining_uses=uses,
        expires_at=expiry,
        is_accessible=is_accessible,
    )
