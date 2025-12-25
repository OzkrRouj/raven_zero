import secrets
from pathlib import Path
from typing import List

from redis.asyncio import Redis

from app.core.logger import logger


class DicewareService:
    def __init__(self, wordlist_path: str | Path = "data/diceware_words.txt"):
        self.wordlist_path = Path(wordlist_path)
        self.wordlist = self._load_wordlist()

        logger.info("diceware_wordlist_loaded", word_count=len(self.wordlist))

    def _load_wordlist(self) -> tuple[str, ...]:
        if not self.wordlist_path.exists():
            logger.error("wordlist_file_not_found", path=str(self.wordlist_path))
            raise FileNotFoundError(f"Wordlist file not found: {self.wordlist_path}")

        words: List[str] = []

        with open(self.wordlist_path, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()

                if not line or line.startswith("#"):
                    continue

                parts = line.split()

                if len(parts) != 2:
                    logger.error("malformed_wordlist_line", line_num=line_num, line=line)
                    raise ValueError(f"Malformed line {line_num}: {line}")

                word = parts[1]
                words.append(word)

        if len(words) != 7776:
            logger.error("wordlist_size_invalid", expected=7776, actual=len(words))
            raise ValueError(f"Wordlist must has 7776 words, has {len(words)}")

        return tuple(words)

    def generate_key(self, word_count: int = 3) -> str:
        words = [secrets.choice(self.wordlist) for _ in range(word_count)]

        return "-".join(words)

    async def generate_unique_key(
        self, redis: Redis, word_count: int = 3, max_attempts: int = 10
    ) -> str:
        for attempt in range(max_attempts):
            key = self.generate_key(word_count)

            exists = await redis.exists(key)

            if not exists:
                logger.info("unique_key_generated", key=key)
                return key

            logger.warning("diceware_collision_detected", key=key, attempt=attempt + 1)

        logger.critical("failed_to_generate_unique_key", max_attempts=max_attempts)
        raise RuntimeError(
            f"Failed to generate unique key after {max_attempts} attempts. "
            f"This should NOT happen (probability: 1 in 10^30)"
        )

    def validate_key_format(self, key: str) -> bool:
        words = key.split("-")

        if len(words) != 3:
            logger.info("key_format_invalid", key=key, word_count=len(words))
            return False

        is_valid = all(word in self.wordlist for word in words)
        if not is_valid:
            logger.info("key_contains_invalid_words", key=key)
        return is_valid

    def get_stats(self) -> dict:
        import math

        size = len(self.wordlist)
        combinations = size**3
        entropy = math.log2(combinations)

        return {
            "wordlist_size": size,
            "combinations_3words": f"{combinations:,}",
            "entropy_bits": round(entropy, 2),
            "wordlist_path": str(self.wordlist_path),
        }


diceware_service = DicewareService()


def generate_key() -> str:
    return diceware_service.generate_key()


async def generate_unique_key(redis: Redis) -> str:
    return await diceware_service.generate_unique_key(redis)
