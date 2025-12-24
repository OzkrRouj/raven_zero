import secrets
from pathlib import Path
from typing import List

from redis.asyncio import Redis


class DicewareService:
    def __init__(self, wordlist_path: str | Path = "data/diceware_words.txt"):
        self.wordlist_path = Path(wordlist_path)
        self.wordlist = self._load_wordlist()

        print(f"✅ Diceware wordlist loaded: {len(self.wordlist)} words")

    def _load_wordlist(self) -> tuple[str, ...]:
        if not self.wordlist_path.exists():
            raise FileNotFoundError(f"Wordlist file not found: {self.wordlist_path}")

        words: List[str] = []

        with open(self.wordlist_path, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()

                if not line or line.startswith("#"):
                    continue

                parts = line.split()

                if len(parts) != 2:
                    raise ValueError(f"Malformed line {line_num}: {line}")

                word = parts[1]
                words.append(word)

        if len(words) != 7776:
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
                return key

            print(f"⚠️  Diceware collision detected: {key} (attempt {attempt + 1})")

        raise RuntimeError(
            f"Failed to generate unique key after {max_attempts} attempts. "
            f"This should NOT happen (probability: 1 in 10^30)"
        )

    def validate_key_format(self, key: str) -> bool:
        words = key.split("-")

        if len(words) != 3:
            return False

        return all(word in self.wordlist for word in words)

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
