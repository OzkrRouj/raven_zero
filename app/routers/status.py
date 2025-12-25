from datetime import datetime, timezone

from fastapi import APIRouter

from app.core.logger import logger
from app.core.redis import get_redis
from app.models.schemas import ErrorResponse, StatusResponse

router = APIRouter(prefix="/status", tags=["Status"])


@router.get(
    "/{key}", response_model=StatusResponse, responses={404: {"model": ErrorResponse}}
)
async def get_file_status(key: str):
    redis = await get_redis()
    data = await redis.hgetall(f"upload:{key}")
    uses = await redis.get(f"upload:{key}:uses")

    if not data:
        logger.info("status_check_not_found", extra={"key": key})
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
