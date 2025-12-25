import hashlib

import aiofiles
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import Response
from redis.asyncio import Redis

from app.core.logger import logger
from app.core.redis import get_redis
from app.core.security import security_service
from app.services.cache import cache_service
from app.services.storage import storage_service

router = APIRouter(prefix="/download", tags=["Download"])


async def task_autodestruction(key: str, redis: Redis):
    logger.info("file_self_destruction_executed", key=key)
    await storage_service.delete_upload(key)
    await cache_service.delete_upload(redis, key)


@router.get("/{key}")
async def download_file(
    key: str, background_tasks: BackgroundTasks, redis: Redis = Depends(get_redis)
):
    remaining = await cache_service.decrement_uses(redis, key)

    if remaining == -2:
        logger.warning("file_not_found_or_expired", key=key)
        raise HTTPException(status_code=404, detail="File not found or link expired")

    if remaining == -1:
        logger.warning("download_limit_reached", key=key)
        raise HTTPException(status_code=410, detail="Download limit has been reached")

    metadata = await cache_service.get_upload_metadata(redis, key)

    if not metadata or "encryption_key" not in metadata:
        logger.error("error_retrieving_security_key", key=key)
        raise HTTPException(status_code=404, detail="Error retrieving security key")

    file_path = await storage_service.get_file_path(
        upload_key=key, filename=metadata["filename"]
    )

    if not file_path:
        logger.error("file_not_exist_on_server", key=key)
        raise HTTPException(status_code=404, detail="File does not exist on the server")

    original_hash = metadata.get("sha256")
    enc_key = metadata.get("encryption_key")

    try:
        async with aiofiles.open(file_path, "rb") as f:
            encrypted_data = await f.read()

            decrypted_data = security_service.decrypt_data(encrypted_data, enc_key)

            current_hash = hashlib.sha256(decrypted_data).hexdigest()

            if original_hash and current_hash != original_hash:
                logger.error("file_integrity_check_failed",
                             key=key,
                             expected_hash=original_hash,
                             actual_hash=current_hash)
                raise HTTPException(
                    status_code=500,
                    detail={
                        "error_code": "INTEGRITY_CHECK_FAILED",
                        "integrity_report": {
                            "expected": original_hash,
                            "actual": current_hash,
                        },
                    },
                )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("decryption_system_error", error=str(e), key=key)
        raise HTTPException(status_code=500, detail="Security error processing file")

    if remaining == 0:
        background_tasks.add_task(task_autodestruction, key, redis)

    logger.info("file_download_success", key=key, filename=metadata["filename"])

    return Response(
        content=decrypted_data,
        media_type=metadata["mime_type"],
        headers={
            "Content-Disposition": f'attachment; filename="{metadata["filename"]}"',
            "X-SHA256": original_hash,
        },
    )
