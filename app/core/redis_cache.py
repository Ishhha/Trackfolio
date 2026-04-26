import redis.asyncio as redis
from app.core.config import settings

# Global redis client instance
redis_client = redis.from_url(settings.redis_url, decode_responses=True)

async def get_redis():
    yield redis_client
