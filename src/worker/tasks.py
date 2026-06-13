"""
Фоновые задачи для arq.
"""

import asyncio
from datetime import datetime

from src.config import settings
from src.core.collector import collect_commits
from src.storage.database import (
    create_request,
    update_request_status,
    find_existing_requests,
)
from src.storage.cache import cache_get, cache_set


async def analyze_github_user(ctx, username: str, period_start: str) -> dict:
    """
    Полный пайплайн анализа GitHub-пользователя.

    1. Проверить кеш
    2. Создать запись в БД
    3. Запустить collector (в отдельном потоке)
    4. Сохранить результат / зафиксировать ошибку
    """
    request_id = ctx["job_id"]
    period_end = datetime.now().strftime("%Y%m%d")
    cache_key = f"github:{username}:{period_start}"

    # 1. Redis cache — самый быстрый путь
    cached = await cache_get(cache_key)
    if cached:
        await create_request(
            request_id=request_id,
            username=username,
            period_start=period_start,
            period_end=period_end,
        )
        await update_request_status(request_id, "done", result_json=cached)
        return {
            "status": "done",
            "request_id": request_id,
            "source": "cache",
            "result_json": cached,
        }

    # 2. Existing request — уже анализировали или анализируем
    existing = await find_existing_requests(username, period_start, period_end)
    if existing:
        if existing["status"] == "processing":
            return {
                "status": "processing",
                "request_id": existing["id"],
                "source": "existing_request",
                "result_json": None,
            }
        if existing["status"] == "done":
            return {
                "status": "done",
                "request_id": existing["id"],
                "source": "deduplicated",
                "result_json": existing["result_json"],
            }

    # 3. Новый запрос — создать и запустить collector
    await create_request(
        request_id=request_id,
        username=username,
        period_start=period_start,
        period_end=period_end,
    )
    await update_request_status(request_id, "processing")

    # 4. Запустить collector в отдельном потоке
    try:
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None,
            collect_commits,
            username,
            period_start,
            settings.max_workers,
        )

        # 5. Успех — сохранить
        result_json = result.model_dump_json()
        await update_request_status(request_id, "done", result_json=result_json)
        await cache_set(cache_key, result_json, ttl=settings.cache_ttl_github)

        return {
            "status": "done",
            "request_id": request_id,
            "cached": False,
            "result_json": result_json,
        }

    except Exception as e:
        # 6. Ошибка — зафиксировать
        await update_request_status(request_id, "failed", error_message=str(e))
        raise