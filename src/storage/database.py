"""
SQLite через SQLAlchemy Core + aiosqlite.
WAL-режим для конкурентного чтения/записи.
"""

import uuid
import asyncio
from datetime import datetime, timezone


from sqlalchemy import (
    MetaData,
    Table,
    Column,
    Text,
)
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
from sqlalchemy import text

from src.config import settings

# ---------- Engine ----------
engine: AsyncEngine = create_async_engine(settings.database_url, echo=False)
metadata = MetaData()
db_lock = asyncio.Lock()


# ---------- Таблицы ----------
requests = Table(
    "requests",
    metadata,
    Column("id", Text, primary_key=True),
    Column("username", Text, primary_key=False),
    Column("period", Text, primary_key=False),
    Column("period_end", Text, primary_key=False),
    Column("status", Text, nullable=False, default="pending"),
    Column("result_json", Text),
    Column("error_message", Text),
    Column("created_at", Text, nullable=False),
    Column("completed_at", Text),
)

commit_cache = Table(
    "commit_cache",
    metadata,
    Column("username", Text, primary_key=True),
    Column("repo", Text, primary_key=True),
    Column("period_start", Text, primary_key=True),
    Column("period_end", Text, primary_key=True),
    Column("data_json", Text, nullable=False),
    Column("cached_at", Text, nullable=False),
)


# ---------- API ----------
async def init_db():
    """Создать таблицы и включить WAL."""
    async with engine.begin() as conn:
        await conn.execute(text("PRAGMA journal_mode=WAL"))
        await conn.run_sync(metadata.create_all)


async def create_request(
    request_id: str,
    username: str,
    period_start: str,
    period_end: str,
) -> str:
    """Создать запрос → вернуть ID."""
    now = datetime.now(timezone.utc).isoformat()

    async with db_lock:
        async with engine.begin() as conn:
            await conn.execute(
                requests.insert().values(
                    id=request_id,
                    username=username,
                    period_start=period_start,
                    period_end=period_end,
                    status="pending",
                    created_at=now,
                )
            )
    return request_id


async def update_request_status(
    request_id: str,
    status: str,
    result_json: str | None = None,
    error_message: str | None = None,
) -> None:
    """Обновить статус и опционально результат."""
    now = datetime.now(timezone.utc).isoformat()
    values = {"status": status, "completed_at": now}
    if result_json:
        values["result_json"] = result_json
    if error_message:
        values["error_message"] = error_message

    async with db_lock:
        async with engine.begin() as conn:
            await conn.execute(
                requests.update().where(requests.c.id == request_id).values(**values)
            )


async def get_request(request_id: str) -> dict | None:
    """Получить запрос по ID."""
    async with engine.connect() as conn:
        result = await conn.execute(
            requests.select().where(requests.c.id == request_id)
        )
        row = result.first()
        return dict(row._mapping) if row else None


async def get_cached_commits(
    username: str,
    repo: str,
    period_start: str,
    period_end: str,
) -> str | None:
    """Достать закешированные коммиты (JSON-строка или None)."""
    async with engine.connect() as conn:
        result = await conn.execute(
            commit_cache.select().where(
                commit_cache.c.username == username,
                commit_cache.c.repo == repo,
                commit_cache.c.period_start == period_start,
                commit_cache.c.period_end == period_end,
            )
        )
        row = result.first()
        return row.data_json if row else None


async def set_cached_commits(
    username: str,
    repo: str,
    period_start: str,
    period_end: str,
    data_json: str,
) -> None:
    """Положить коммиты в кеш."""
    now = datetime.now(timezone.utc).isoformat()

    async with db_lock:
        async with engine.begin() as conn:
            await conn.execute(
                commit_cache.insert().values(
                    username=username,
                    repo=repo,
                    period_start=period_start,
                    period_end=period_end,
                    data_json=data_json,
                    cached_at=now,
                )
            )
