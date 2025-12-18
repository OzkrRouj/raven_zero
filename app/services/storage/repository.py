import asyncio
import shutil
from abc import ABC, abstractmethod
from pathlib import Path

import aiofiles
import aiofiles.os


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

            print(f"✓ File Saved: {path}")
            return True

        except Exception as e:
            print(f"✗ Error saving file: {e}")
            return False

    async def exists(self, path: Path) -> bool:
        return await aiofiles.os.path.exists(path)

    async def delete(self, path: Path) -> bool:
        try:
            if await self.exists(path):
                await aiofiles.os.remove(path)
                print(f"✓ File deleted: {path}")
                return True

            print(f"⚠️  File does not exist: {path}")
            return False

        except Exception as e:
            print(f"✗ Error deleting file: {e}")
            return False

    async def delete_directory(self, path: Path) -> bool:
        try:
            if await self.exists(path):
                await asyncio.to_thread(shutil.rmtree, path)
                print(f"✓ Directory deleted: {path}")
                return True

            print(f"⚠️  Directory does not exist: {path}")
            return False
        except Exception as e:
            print(f"✗ Error deleting directory: {e}")
            return False
