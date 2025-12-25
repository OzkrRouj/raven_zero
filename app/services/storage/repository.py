import asyncio
import shutil
from abc import ABC, abstractmethod
from pathlib import Path

import aiofiles
import aiofiles.os

from app.core.logger import logger


class FileRepository(ABC):
    @abstractmethod
    async def save(self, content: bytes, path: Path) -> bool:
        pass

    @abstractmethod
    async def exists(self, path: Path) -> bool:
        pass

    @abstractmethod
    async def delete(self, path: Path) -> bool:
        pass


class LocalFileRepository(FileRepository):
    async def save(self, content: bytes, path: Path) -> bool:
        try:
            path.parent.mkdir(exist_ok=True, parents=True)

            async with aiofiles.open(path, "wb") as f:
                await f.write(content)

            logger.info("file_saved", file_path=str(path))
            return True

        except Exception as e:
            logger.error("error_saving_file", file_path=str(path), error=str(e))
            return False

    async def exists(self, path: Path) -> bool:
        return await aiofiles.os.path.exists(path)

    async def delete(self, path: Path) -> bool:
        try:
            if await self.exists(path):
                await aiofiles.os.remove(path)
                logger.info("file_deleted", file_path=str(path))
                return True

            logger.warning("file_does_not_exist", file_path=str(path))
            return False

        except Exception as e:
            logger.error("error_deleting_file", file_path=str(path), error=str(e))
            return False

    async def delete_directory(self, path: Path) -> bool:
        try:
            if await self.exists(path):
                await asyncio.to_thread(shutil.rmtree, path)
                logger.info("directory_deleted", directory_path=str(path))
                return True

            logger.warning("directory_does_not_exist", directory_path=str(path))
            return False
        except Exception as e:
            logger.error("error_deleting_directory", directory_path=str(path), error=str(e))
            return False
