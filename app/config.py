from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Setings(BaseSettings):
    """
    Everything that changes or defines the environment,
    you declare and validate it here;
    the code only executes the logic.
    """

    redis_url: str = Field(description="Redis URL", default="redis://localhost:6379/0")

    @field_validator("redis_url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        if not v.startswith("redis://"):
            raise ValueError(f"redis_url must start with 'redis://'url used: {v}")

    storage_path: str = Field(
        description="Directory for store uplads", default="./storage/uplad"
    )

    diceware_wordlist_path: Path = Path("data/diceware_words.txt")

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )
