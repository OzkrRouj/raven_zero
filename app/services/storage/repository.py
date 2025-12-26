import asyncio
import os
import shutil
from abc import ABC, abstractmethod
from pathlib import Path

import aiofiles
import aiofiles.os

from app.config import settings
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

            logger.info("file_saved")
            return True

        except Exception as e:
            logger.error("error_saving_file", error=str(e))
            return False

    async def exists(self, path: Path) -> bool:
        return await aiofiles.os.path.exists(path)

    async def _shred_file(self, path: Path, passes: int = 1):
        try:
            if not await self.exists(path):
                return

            file_size = (await aiofiles.os.stat(path)).st_size

            async with aiofiles.open(path, "ba+", buffering=0) as f:
                for _ in range(passes):
                    await f.seek(0)
                    await f.write(os.urandom(file_size))
                    os.fsync(f.fileno())

            logger.debug("file_shredded", path=str(path))
        except Exception as e:
            logger.error("error_shredding_file", path=str(path), error=str(e))

    async def delete(self, path: Path) -> bool:
        try:
            if await self.exists(path):
                await self._shred_file(path, passes=settings.secure_shred_passes)
                await aiofiles.os.remove(path)
                logger.info("file_deleted")
                return True

            logger.warning("file_does_not_exist")
            return False

        except Exception as e:
            logger.error("error_deleting_file", error=str(e))
            return False

    async def delete_directory(self, path: Path) -> bool:
        try:
            if await self.exists(path):
                for root, dirs, files in os.walk(path, topdown=False):
                    for name in files:
                        file_to_shred = Path(root) / name
                        await self._shred_file(
                            file_to_shred, passes=settings.secure_shred_passes
                        )

                await asyncio.to_thread(shutil.rmtree, path)
                logger.info("directory_deleted")
                return True

            logger.warning("directory_does_not_exist")
            return False
        except Exception as e:
            logger.error("error_deleting_directory", error=str(e))
            return False
