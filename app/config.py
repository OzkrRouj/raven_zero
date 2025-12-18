from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Everything that changes or defines the environment,
    you declare and validate it here;
    the code only executes the logic.
    """

    # --- INFRASTRUCTURE ---
    redis_url: str = Field(
        default="redis://localhost:6379/0", description="Redis connection string"
    )

    @field_validator("redis_url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        if not v.startswith("redis://"):
            raise ValueError(f"redis_url must start with 'redis://'. URL used: {v}")
        return v

    # --- FILE ROUTES ---
    storage_path: Path = Field(
        default=Path("./storage/uploads"), description="Directory for storing uploads"
    )

    diceware_wordlist_path: Path = Field(
        default=Path("data/diceware_words.txt"),
        description="Path to the diceware dictionary file",
    )

    @field_validator("diceware_wordlist_path")
    @classmethod
    def check_file_exists(cls, v: Path) -> Path:
        if not v.exists():
            raise ValueError(f"Wordlist file not found at: {v}")
        return v

    allowed_mime_types: list[str] = Field(
        default=[], description="List of allowed MIME types"
    )

    max_file_size: int = Field(
        default=10 * 1024 * 1024, description="Maximum file size in bytes"
    )

    # --- CONFIGURATION ---
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )


settings = Settings()
