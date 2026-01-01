import asyncpg
from .config import settings
from pathlib import Path

_pool: asyncpg.Pool | None = None

async def connect():
    global _pool
    _pool = await asyncpg.create_pool(dsn=settings.DATABASE_URL, min_size=1, max_size=10)

async def close():
    global _pool
    if _pool:
        await _pool.close()

def pool() -> asyncpg.Pool:
    assert _pool is not None, "DB pool not initialized"
    return _pool

async def init_schema():
    sql_path = Path(__file__).parent / "sql" / "001_init.sql"
    ddl = sql_path.read_text(encoding="utf-8")
    async with pool().acquire() as conn:
        await conn.execute(ddl)

async def get_topics(limit: int = 100):
    q = "SELECT DISTINCT topic FROM events ORDER BY topic LIMIT $1"
    async with pool().acquire() as conn:
        rows = await conn.fetch(q, limit)
    return [r["topic"] for r in rows]
