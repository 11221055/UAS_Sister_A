import json
from redis.asyncio import Redis
from .config import settings

_redis: Redis | None = None

async def connect_redis():
    global _redis
    _redis = Redis.from_url(settings.REDIS_URL, decode_responses=True)

async def close_redis():
    global _redis
    if _redis:
        await _redis.close()

def redis() -> Redis:
    assert _redis is not None, "Redis not initialized"
    return _redis

async def enqueue_events(events: list[dict]):
    # RPUSH for each event JSON
    r = redis()
    q = settings.QUEUE_NAME
    pipe = r.pipeline()
    for e in events:
        pipe.rpush(q, json.dumps(e))
    await pipe.execute()

async def dequeue(timeout: int = 1):
    # BLPOP returns (queue, item) or None
    r = redis()
    return await r.blpop(settings.QUEUE_NAME, timeout=timeout)
