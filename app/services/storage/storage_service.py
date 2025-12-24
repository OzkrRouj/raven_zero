from pathlib import Path
from typing import Optional, Tuple

from fastapi import HTTPException, UploadFile

from app.config import settings
from app.core.security import security_service

from .mime_detector import MagicMimeDetector, MimeDetector
from .path_manager import StoragePathManager
from .repository import FileRepository, LocalFileRepository
from .sanitizer import FilenameSanitizer, SecurityFilenameSanitizer
from .validators import FileMimeTypeValidator, FileSizeValidator, FileValidationService


class StorageService:
    def __init__(
        self,
        path_manager: StoragePathManager = None,
        repository: FileRepository = None,
        mime_detector: MimeDetector = None,
        sanitizer: FilenameSanitizer = None,
        validator: FileValidationService = None,
    ):
        self.path_manager = path_manager or StoragePathManager(settings.storage_path)

        self.repository = repository or LocalFileRepository()

        self.mime_detector = mime_detector or MagicMimeDetector()

        self.sanitizer = sanitizer or SecurityFilenameSanitizer()

        if validator is None:
            self.validator = FileValidationService()

            self.validator.add_validator(FileSizeValidator(settings.max_file_size))

            if hasattr(settings, "allowed_mime_types"):
                self.validator.add_validator(
                    FileMimeTypeValidator(settings.allowed_mime_types)
                )
        else:
            self.validator = validator

    async def save_file(
        self,
        file: UploadFile,
        upload_key: str,
        encryption_key: str,
    ) -> Tuple[str, str, int]:
        try:
            print(f"📤 Starting file save: {file.filename}")

            print("  → Reading content...")
            content = await file.read()
            print(f"  ✓ Read: {len(content):,} bytes")

            print("  → Detecting MIME type...")
            mime_type = await self.mime_detector.detect(content, file.content_type)
            print(f"  ✓ Detected type: {mime_type}")

            print("  → Validating file...")
            metadata = {"mime_type": mime_type, "filename": file.filename}

            is_valid, error_msg = await self.validator.validate_all(content, metadata)

            if not is_valid:
                print(f"  ✗ Validation failed: {error_msg}")
                raise HTTPException(status_code=400, detail=error_msg)

            print("  ✓ Validation successful")

            print("  → Sanitizing filename...")
            safe_filename = self.sanitizer.sanitize(file.filename)
            print(f"  ✓ Safe filename: {safe_filename}")

            file_path = self.path_manager.get_file_path(upload_key, safe_filename)
            print(f"  → Saving to: {file_path}")

            encrypted_content = security_service.encrypt_data(content, encryption_key)

            success = await self.repository.save(encrypted_content, file_path)

            if not success:
                raise HTTPException(
                    status_code=500, detail="Error saving file to repository"
                )

            print("✅ File saved successfully")

            return str(file_path), mime_type, len(content)

        except HTTPException:
            raise

        except Exception as e:
            print(f"❌ Unexpected error: {e}")

            await self.cleanup_upload(upload_key)

            raise HTTPException(status_code=500, detail=f"Error saving file: {str(e)}")

    async def get_file_path(self, upload_key: str, filename: str) -> Optional[Path]:
        safe_filename = self.sanitizer.sanitize(filename)

        file_path = self.path_manager.get_file_path(upload_key, safe_filename)

        if await self.repository.exists(file_path):
            return file_path

        return None

    async def delete_upload(self, upload_key: str) -> bool:
        print(f"🗑️  Deleting upload: {upload_key}")

        upload_dir = self.path_manager.get_upload_directory(upload_key)

        success = await self.repository.delete_directory(upload_dir)

        if success:
            print(f"✅ Upload deleted: {upload_key}")
        else:
            print(f"⚠️  Upload did not exist: {upload_key}")

        return success

    async def cleanup_upload(self, upload_key: str):
        """
        Cleans up an upload (alias for delete_upload).

        Use this when there are errors during the upload process.
        """
        await self.delete_upload(upload_key)
