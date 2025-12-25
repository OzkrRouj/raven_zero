import hashlib
from pathlib import Path
from typing import Optional, Tuple

from fastapi import HTTPException, UploadFile

from app.config import settings
from app.core.logger import logger
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
            logger.info("starting_file_save", filename=file.filename, key=upload_key)

            logger.debug("reading_file_content", filename=file.filename)
            content = await file.read()
            logger.debug("file_content_read", filename=file.filename, size=len(content))

            logger.debug("detecting_mime_type", filename=file.filename)
            mime_type = await self.mime_detector.detect(content, file.content_type)
            logger.debug("mime_type_detected", filename=file.filename, mime_type=mime_type)

            logger.debug("validating_file", filename=file.filename)
            metadata = {"mime_type": mime_type, "filename": file.filename}

            file_hash = hashlib.sha256(content).hexdigest()

            is_valid, error_msg = await self.validator.validate_all(content, metadata)

            if not is_valid:
                logger.warning("file_validation_failed", filename=file.filename, error_msg=error_msg)
                raise HTTPException(status_code=400, detail=error_msg)

            logger.debug("file_validation_successful", filename=file.filename)

            logger.debug("sanitizing_filename", filename=file.filename)
            safe_filename = self.sanitizer.sanitize(file.filename)
            logger.debug("filename_sanitized", original_filename=file.filename, safe_filename=safe_filename)

            file_path = self.path_manager.get_file_path(upload_key, safe_filename)
            logger.debug("saving_file_to_path", file_path=str(file_path))

            encrypted_content = security_service.encrypt_data(content, encryption_key)

            success = await self.repository.save(encrypted_content, file_path)

            if not success:
                logger.error("error_saving_file_to_repository", file_path=str(file_path))
                raise HTTPException(
                    status_code=500, detail="Error saving file to repository"
                )

            logger.info("file_saved_successfully", file_path=str(file_path), key=upload_key)

            return str(file_path), mime_type, len(content), file_hash

        except HTTPException:
            raise

        except Exception as e:
            logger.error("unexpected_error_during_file_save", filename=file.filename, key=upload_key, error=str(e))

            await self.cleanup_upload(upload_key)

            raise HTTPException(status_code=500, detail=f"Error saving file: {str(e)}")

    async def get_file_path(self, upload_key: str, filename: str) -> Optional[Path]:
        safe_filename = self.sanitizer.sanitize(filename)

        file_path = self.path_manager.get_file_path(upload_key, safe_filename)

        if await self.repository.exists(file_path):
            return file_path

        return None

    async def delete_upload(self, upload_key: str) -> bool:
        logger.info("deleting_upload", key=upload_key)

        upload_dir = self.path_manager.get_upload_directory(upload_key)

        success = await self.repository.delete_directory(upload_dir)

        if success:
            logger.info("upload_deleted", key=upload_key)
        else:
            logger.warning("upload_not_exist", key=upload_key)

        return success

    async def cleanup_upload(self, upload_key: str):
        """
        Cleans up an upload (alias for delete_upload).

        Use this when there are errors during the upload process.
        """
        await self.delete_upload(upload_key)
