import os, random, asyncio
import httpx
from datetime import datetime, timezone

TARGET = os.getenv("TARGET_URL", "http://localhost:8080/publish")
TOTAL = int(os.getenv("TOTAL", "20000"))
DUP_RATE = float(os.getenv("DUP_RATE", "0.3"))
TOPICS = os.getenv("TOPICS", "app.auth,app.pay").split(",")

BATCH = 200  # TODO: tuning

def make_event(i: int, topic: str, event_id: str):
    return {
        "topic": topic,
        "event_id": event_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source": "publisher",
        "payload": {"i": i, "msg": "hello"}
    }

async def main():
    sent_ids = []
    async with httpx.AsyncClient(timeout=30) as client:
        i = 0
        while i < TOTAL:
            batch = []
            for _ in range(BATCH):
                if i >= TOTAL:
                    break
                topic = random.choice(TOPICS)
                if sent_ids and random.random() < DUP_RATE:
                    # resend existing id -> duplikasi
                    event_id = random.choice(sent_ids)
                else:
                    event_id = f"{topic}-{i}-{random.randint(1, 10_000_000)}"
                    sent_ids.append(event_id)

                batch.append(make_event(i, topic, event_id))
                i += 1

            # TODO: retry/backoff minimal
            r = await client.post(TARGET, json=batch)
            r.raise_for_status()

if __name__ == "__main__":
    asyncio.run(main())
