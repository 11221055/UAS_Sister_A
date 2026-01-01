import httpx, pytest, time

@pytest.mark.asyncio
async def test_dedup_single(base_url):
    e = {
      "topic":"app.auth","event_id":"fixed-1",
      "timestamp":"2025-01-01T00:00:00Z","source":"t","payload":{"a":1}
    }
    async with httpx.AsyncClient() as c:
        r1 = await c.post(f"{base_url}/publish", json=[e])
        r2 = await c.post(f"{base_url}/publish", json=[e])
        assert r1.status_code in (200,202)
        assert r2.status_code in (200,202)

        # beri waktu worker memproses
        time.sleep(1)

        ev = await c.get(f"{base_url}/events", params={"topic":"app.auth"})
        assert ev.status_code == 200
        rows = [x for x in ev.json() if x["event_id"] == "fixed-1"]
        assert len(rows) == 1
