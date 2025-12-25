from typing import Optional

from redis.asyncio import Redis

from app.core.logger import logger


class CacheService:
    @staticmethod
    async def save_upload_metadata(
        redis: Redis, key: str, metadata: dict, ttl_seconds: int, encryption_key: str
    ) -> bool:
        try:
            uses = metadata.pop("uses", 3)

            metadata["encryption_key"] = encryption_key

            async with redis.pipeline(transaction=True) as pipe:
                pipe.hset(
                    f"upload:{key}", mapping={k: str(v) for k, v in metadata.items()}
                )

                pipe.set(f"upload:{key}:uses", uses)
                pipe.set(f"upload:{key}:previewed", "false")

                pipe.expire(f"upload:{key}", ttl_seconds)
                pipe.expire(f"upload:{key}:uses", ttl_seconds)
                pipe.expire(f"upload:{key}:previewed", ttl_seconds)

                await pipe.execute()

            logger.info("metadata_saved", key=key)
            return True
        except Exception as e:
            logger.error("error_saving_metadata", key=key, error=str(e))
            raise

    @staticmethod
    async def get_upload_metadata(
        redis: Redis,
        key: str,
    ) -> Optional[dict]:
        try:
            async with redis.pipeline() as pipe:
                pipe.hgetall(f"upload:{key}")
                pipe.get(f"upload:{key}:uses")
                pipe.get(f"upload:{key}:previewed")

                res = await pipe.execute()

            data, uses, previewed = res

            if not data:
                logger.warning("metadata_not_found", key=key)
                return None

            logger.info("metadata_retrieved", key=key)
            return {
                **data,
                "uses": int(uses) if uses else 0,
                "previewed": previewed == "true",
            }

        except Exception as e:
            logger.error("error_getting_metadata", key=key, error=str(e))
            raise

    @staticmethod
    async def decrement_uses(redis: Redis, key: str) -> int:
        lua_script = """
            local uses = redis.call('GET', KEYS[1])
            if not uses then return -2 end
            uses = tonumber(uses)
            if uses > 0 then
                return redis.call('DECR', KEYS[1])
            else
                return -1
            end
        """

        resoult = await redis.eval(lua_script, 1, f"upload:{key}:uses")
        return int(resoult)

    @staticmethod
    async def mark_as_previewed_atomic(redis: Redis, key: str) -> bool:
        preview_key = f"upload:{key}:previewed"
        exists = await redis.exists(preview_key)
        if not exists:
            return False

        old_value = await redis.getset(preview_key, "true")

        return old_value == b"false" or old_value == "false"

    @staticmethod
    async def delete_upload(redis: Redis, key: str) -> bool:
        try:
            deleted = await redis.delete(
                f"upload:{key}", f"upload:{key}:uses", f"upload:{key}:previewed"
            )

            return deleted > 0
        except Exception:
            return False

    @staticmethod
    async def get_ttl(redis: Redis, key: str) -> int:
        try:
            ttl = await redis.ttl(f"upload:{key}")
            return ttl if ttl > 0 else -1
        except Exception:
            return -1

    @staticmethod
    async def exists(redis: Redis, key: str) -> bool:
        try:
            return await redis.exists(f"upload:{key}") > 0
        except Exception:
            return False


cache_service = CacheService()
