from abc import ABC, abstractmethod


class FileValidator(ABC):
    @abstractmethod
    async def validate(
        self,
        content: bytes,
        metadata: dict,
    ) -> tuple[bool, str]:
        pass


class FileSizeValidator(FileValidator):
    def __init__(self, max_size: int):
        self.max_size = max_size

    async def validate(
        self,
        content: bytes,
        metadata: dict,
    ) -> tuple[bool, str]:
        file_size = len(content)

        if file_size > self.max_size:
            error_msg = (
                f"File too large: {file_size:,} bytes "
                f"(Max Size: {self.max_size:,} bytes)"
            )
            return False, error_msg

        return True, ""


class FileMimeTypeValidator(FileValidator):
    def __init__(self, allowed_types: list[str]):
        self.allowed_types = allowed_types or []

    async def validate(
        self,
        content: bytes,
        metadata: dict,
    ) -> tuple[bool, str]:
        if not self.allowed_types:
            return True, ""

        mime_type = metadata.get("mime_type")

        if not mime_type:
            return False, "MIME not delcared"

        if mime_type in self.allowed_types:
            return True, ""

        for allowed in self.allowed_types:
            if "*" in allowed:
                category = allowed.split("/")[0]
                if mime_type.startswith(f"{category}/"):
                    return True, ""

        return False, f"File type not suported: {mime_type}"


class FileValidationService:
    def __init__(self, validators: list[FileValidator] = None):
        self.validators = validators or []

    def add_validator(self, validator: FileValidator):
        self.validators.append(validator)

    async def validate(
        self,
        content: bytes,
        metadata: dict,
    ) -> tuple[bool, str]:
        for validator in self.validators:
            is_valid, error_msg = await validator.validate(content, metadata)

            if not is_valid:
                return False, error_msg

            return True, ""

    async def validate_all(self, content: bytes, metadata: dict) -> tuple[bool, str]:
        for validator in self.validators:
            is_valid, error_msg = await validator.validate(content, metadata)

            if not is_valid:
                return False, error_msg

        return True, ""
