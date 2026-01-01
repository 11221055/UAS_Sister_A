import asyncio, json, time
from .db import pool
from .queue import dequeue

async def process_one(event: dict) -> tuple[bool, str]:
    """
    Return (is_unique_processed, reason)
    """
    topic = event["topic"]
    event_id = event["event_id"]
    source = event["source"]
    ts = event["timestamp"]
    payload = event["payload"]

    async with pool().acquire() as conn:
        async with conn.transaction():  # default READ COMMITTED
            # 1) received selalu naik (atomik)
            await conn.execute("UPDATE stats SET received = received + 1 WHERE id = 1")

            # 2) dedup gate
            inserted = await conn.fetchval(
                """
                INSERT INTO processed_events(topic, event_id, source)
                VALUES ($1, $2, $3)
                ON CONFLICT DO NOTHING
                RETURNING 1
                """,
                topic, event_id, source
            )

            if inserted == 1:
                # unique: simpan event
                await conn.execute(
                    """
                    INSERT INTO events(topic, event_id, ts, source, payload)
                    VALUES ($1, $2, $3, $4, $5)
                    ON CONFLICT (topic, event_id) DO NOTHING
                    """,
                    topic, event_id, ts, source, payload
                )
                await conn.execute("UPDATE stats SET unique_processed = unique_processed + 1 WHERE id = 1")
                return True, "unique"
            else:
                await conn.execute("UPDATE stats SET duplicate_dropped = duplicate_dropped + 1 WHERE id = 1")
                return False, "duplicate"

async def worker_loop(worker_id: int, stop: asyncio.Event):
    while not stop.is_set():
        item = await dequeue(timeout=1)
        if not item:
            continue

        _, raw = item
        try:
            event = json.loads(raw)
            await process_one(event)
            # TODO: logging ringkas: worker_id, topic, event_id, unique/duplicate
        except Exception as e:
            # TODO: retry/backoff atau DLQ (opsional)
            # minimal: log error
            pass
