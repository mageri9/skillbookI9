"""Кеш на Redis — get/set с TTL."""

from src.logger import get_logger
from src.storage.redis import get_redis

logger = get_logger(__name__)


async def cache_get(key: str) -> str | None:
    """Получить значение. None если ключа нет или Redis недоступен."""
    try:
        r = await get_redis()
        return await r.get(key)
    except Exception as e:
        logger.warning(f"cache_get({key!r}) failed: {e}")
        return None


async def cache_set(key: str, value: str, ttl: int = 3600) -> None:
    """Записать значение с TTL в секундах."""
    try:
        r = await get_redis()
        await r.set(key, value, ex=ttl)
    except Exception as e:
        logger.warning(f"cache_set({key!r}) failed: {e}")