from redis.asyncio import Redis

from app.config import settings

redis_client = Redis.from_url(
    settings.redis_url,
    decode_responses=True,
    health_check_interval=30,
    socket_connect_timeout=5,
    socket_keepalive=True,
    max_connections=10,
)


async def get_redis():
    return redis_client
