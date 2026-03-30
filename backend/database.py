import os
from typing import Optional

import asyncpg

_pool: Optional[asyncpg.Pool] = None


async def connect() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        dsn = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/postgres")
        _pool = await asyncpg.create_pool(dsn)
    return _pool


async def disconnect() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


async def get_pool() -> asyncpg.Pool:
    return await connect()
