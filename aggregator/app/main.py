import asyncio, time
from fastapi import FastAPI, Query
from typing import List, Optional
from .config import settings
from .schema import Event, PublishResponse, StatsResponse
from .db import connect, close, init_schema, pool, get_topics
from .queue import connect_redis, close_redis, enqueue_events
from .worker import worker_loop

app = FastAPI(title="Distributed PubSub Log Aggregator")

_started = time.time()
_stop = asyncio.Event()
_tasks: list[asyncio.Task] = []

@app.on_event("startup")
async def on_startup():
    await connect()
    await init_schema()
    await connect_redis()

    # start workers
    for i in range(settings.WORKERS):
        _tasks.append(asyncio.create_task(worker_loop(i, _stop)))

@app.on_event("shutdown")
async def on_shutdown():
    _stop.set()
    for t in _tasks:
        t.cancel()
    await close_redis()
    await close()

@app.post("/publish", response_model=PublishResponse)
async def publish(events: List[Event]):
    # terima batch; FastAPI sudah validasi
    payload = [e.model_dump(mode="json") for e in events]
    await enqueue_events(payload)
    return PublishResponse(received=len(payload), enqueued=len(payload))

@app.get("/events")
async def list_events(topic: Optional[str] = Query(default=None)):
    q = "SELECT topic, event_id, ts as timestamp, source, payload FROM events"
    args = []
    if topic:
        q += " WHERE topic = $1"
        args = [topic]
    q += " ORDER BY ts ASC LIMIT 5000"  # TODO: pagination kalau mau

    async with pool().acquire() as conn:
        rows = await conn.fetch(q, *args)
    return [dict(r) for r in rows]

@app.get("/stats", response_model=StatsResponse)
async def stats():
    async with pool().acquire() as conn:
        row = await conn.fetchrow("SELECT received, unique_processed, duplicate_dropped, started_at FROM stats WHERE id=1")
    topics = await get_topics()
    uptime = int(time.time() - _started)
    return StatsResponse(
        received=row["received"],
        unique_processed=row["unique_processed"],
        duplicate_dropped=row["duplicate_dropped"],
        topics=topics,
        uptime_seconds=uptime
    )
