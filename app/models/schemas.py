from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field


class UploadRequest(BaseModel):
    expiry: int = Field(
        default=10,
        ge=1,
        le=60,
        description="Expiry time in minutes",
        examples=[1, 5, 10, 30, 60],
    )

    uses: int = Field(
        default=3,
        ge=1,
        le=5,
        description="Number of times the file can be downloaded",
        examples=[1, 3, 5],
    )

    model_config = ConfigDict(json_schema_extra={"example": {"expiry": 10, "uses": 3}})


class UploadResponse(BaseModel):
    key: str = Field(
        description="Unique diceware file key",
        examples=["correct-horse-battery", "apple-pie-pancake"],
    )

    preview_url: str = Field(
        description="URL to the file preview",
        examples=["https://raven.zero/preview/correct-horse-battery"],
    )

    download_url: str = Field(
        description="URL to the file download",
        examples=["https://raven.zero/download/correct-horse-battery"],
    )

    expiry: datetime = Field(
        description="Expiry time of the file", examples=["2025-12-18T14:04:00.000Z"]
    )

    uses: int = Field(
        description="Number of times the file can be downloaded",
        ge=1,
        le=5,
        examples=[1, 3, 5],
    )

    filename: str = Field(
        description="Original filename",
        examples=["document.pdf", "config.json"],
    )

    size: int = Field(
        description="File size in bytes",
        gt=0,
        examples=[51200, 1048576],
    )

    created_at: datetime = Field(
        description="Creation timestamp (UTC)",
        examples=["2024-12-10T15:50:00Z"],
    )

    sha256: str = Field(description="SHA-256 hash of the original file")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "key": "correct-horse-battery",
                "preview_url": "https://raven.zero/preview/correct-horse-battery",
                "download_url": "https://raven.zero/download/correct-horse-battery",
                "expiry": "2024-12-10T16:00:00Z",
                "uses": 3,
                "filename": "document.pdf",
                "size": 51200,
                "created_at": "2024-12-10T15:50:00Z",
                "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            }
        }
    )


class PreviewResponse(BaseModel):
    key: str = Field(description="Diceware key")
    filename: str = Field(description="Filename")
    size: int = Field(description="File size in bytes", gt=0)
    mime_type: str = Field(description="File MIME type")
    expiry: datetime = Field(description="Expiration time")
    uses: int = Field(description="Remaining downloads", ge=0)
    minutes_left: int = Field(description="Minutes until expiration", ge=0)
    download_url: str = Field(description="Download URL")
    curl_example: str = Field(description="cURL command example")
    created_at: datetime = Field(description="Upload time")
    sha256: str = Field(description="SHA-256 hash for integrity verification")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "key": "correct-horse-battery",
                "filename": "document.pdf",
                "size": 51200,
                "mime_type": "application/pdf",
                "expiry": "2024-12-10T16:00:00Z",
                "uses": 3,
                "minutes_left": 8,
                "download_url": "https://raven.zero/download/correct-horse-battery",
                "curl_example": "curl -O https://raven.zero/download/correct-horse-battery",
                "created_at": "2024-12-10T15:50:00Z",
                "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            }
        }
    )


class ErrorResponse(BaseModel):
    detail: str = Field(
        description="Human-readable error message",
        examples=[
            "File too large (max 1MB)",
            "File type not allowed",
            "Upload not found or expired",
        ],
    )


class HealthResponse(BaseModel):
    """Schema for /health endpoint"""

    status: str = Field(description="Estado general", examples=["healthy", "degraded"])
    version: str = Field(default="0.1.0")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    services: dict[str, str] = Field(
        description="Estado detallado de cada componente",
        examples=[{"redis": "online", "storage": "online", "diceware": "online"}],
    )
    uptime_seconds: int = Field(description="Seconds since start")
    started_at: datetime | None = Field(
        default=None, description="App start time (UTC)"
    )


class StatusResponse(BaseModel):
    key: str = Field(description="Clave del archivo")
    status: str = Field(
        description="Estado actual del archivo",
        examples=["active", "burned", "expired"],
    )
    remaining_uses: int = Field(default=0, description="Descargas restantes")
    expires_at: datetime | None = Field(
        default=None, description="Fecha de expiración original"
    )
    is_accessible: bool = Field(
        description="Indica si el archivo se puede descargar actualmente"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "key": "correct-horse-battery",
                "status": "active",
                "remaining_uses": 2,
                "expires_at": "2025-12-25T18:00:00Z",
                "is_accessible": True,
            }
        }
    )
