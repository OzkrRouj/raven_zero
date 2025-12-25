from pathlib import Path

from app.core.logger import logger


class StoragePathManager:
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.temp_path = self.base_path / "temp"

        self._ensure_directories()

    def _ensure_directories(self):
        self.base_path.mkdir(exist_ok=True, parents=True)
        self.temp_path.mkdir(exist_ok=True)

        logger.info("storage_directories_ready")

    def get_upload_directory(self, upload_key: str) -> Path:
        return self.base_path / upload_key

    def get_file_path(self, upload_key: str, filename: str) -> Path:
        return self.get_upload_directory(upload_key) / filename

    def get_temp_path(self, temp_id: str) -> Path:
        return self.temp_path / temp_id
