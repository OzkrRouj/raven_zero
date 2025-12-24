from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Form, HTTPException, Request, UploadFile
from redis.asyncio import Redis

from app.core.redis import get_redis
from app.core.security import security_service
from app.models.schemas import UploadResponse
from app.services.cache import cache_service
from app.services.diceware import diceware_service
from app.services.storage import storage_service

router = APIRouter(
    prefix="/upload",
    tags=["Upload"],
)


@router.post(
    "/",
    response_model=UploadResponse,
    status_code=201,
    summary="Upload a file",
    description="Upload a file with auto-destruction parameters",
)
async def upload_file(
    request: Request,
    file: UploadFile,
    expiry: int = Form(default=10, ge=1, le=60, description="Minutes until expiration"),
    uses: int = Form(default=1, ge=1, le=5, description="Number of downloads allowed"),
    redis: Redis = Depends(get_redis),
):
    key = None
    file_saved = False

    try:
        print(f"📤 Starting upload: {file.filename}")

        key = await diceware_service.generate_unique_key(redis)
        enc_key = security_service.generate_key()
        print(f"  ✓ Key generated: {key}")

        file_path, mime_type, size = await storage_service.save_file(
            file=file, upload_key=key, encryption_key=enc_key
        )

        file_saved = True
        print(f"  ✓ File validated and saved to: {file_path}")

        now = datetime.now(timezone.utc)
        expiry_dt = now + timedelta(minutes=expiry)
        ttl_seconds = expiry * 60

        metadata = {
            "filename": file.filename,
            "size": size,
            "mime_type": mime_type,
            "created_at": now.isoformat(),
            "expiry_at": expiry_dt.isoformat(),
            "uses": uses,
        }

        await cache_service.save_upload_metadata(
            redis=redis,
            key=key,
            metadata=metadata,
            ttl_seconds=ttl_seconds,
            encryption_key=enc_key,
        )
        print("  ✓ Metadata saved to Redis")

        base_url = str(request.base_url).rstrip("/")

        return UploadResponse(
            key=key,
            preview_url=f"{base_url}/preview/{key}",
            download_url=f"{base_url}/download/{key}",
            expiry=expiry_dt,
            uses=uses,
            filename=file.filename,
            size=size,
            created_at=now,
        )
    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        print(f"❌ Critical upload error: {str(e)}")

        if file_saved and key:
            await storage_service.delete_upload(key)
            print(f"🔄 Rollback executed: File {key} deleted")

        raise HTTPException(
            status_code=500, detail=f"Internal error while processing upload: {str(e)}"
        )
