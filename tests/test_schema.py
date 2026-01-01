import httpx
import pytest

@pytest.mark.asyncio
async def test_invalid_schema_missing_topic(base_url):
    bad = [{
        "event_id": "x"*8,
        "timestamp": "2025-01-01T00:00:00Z",
        "source": "t",
        "payload": {}
    }]
    async with httpx.AsyncClient() as c:
        r = await c.post(f"{base_url}/publish", json=bad)
    assert r.status_code in (400, 422)
