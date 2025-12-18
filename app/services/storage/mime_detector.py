from abc import ABC, abstractmethod
from typing import Optional

import magic


class MimeDetector(ABC):
    @abstractmethod
    async def detect(self, content: bytes, declared_type: Optional[str]) -> str:
        pass


class MagicMimeDetector(MimeDetector):
    async def detect(self, content: bytes, declared_type: Optional[str]) -> str:
        try:
            mime = magic.Magic(mime=True)
            detected = mime.from_buffer(content[:1024])
            return detected

        except Exception as e:
            print(f"⚠️  Error detecting MIME type: {e}")
            return declared_type or "application/octet-stream"
