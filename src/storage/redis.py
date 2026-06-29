"""
Единый Redis-клиент для всего проекта.

Один синглтон на процесс — cache.py и pubsub.py импортируют отсюда.
Два отдельных клиента нужны только для pub/sub: Redis-протокол требует
выделенного соединения для SUBSCRIBE (оно блокируется на listen).
Для обычных команд (GET/SET/PUBLISH) используется общий _client.
"""

import redis.asyncio as aioredis

from src.config import settings
from src.logger import get_logger

logger = get_logger(__name__)

# Общий клиент — GET, SET, PUBLISH, произвольные команды
_client: aioredis.Redis | None = None


def _make_client() -> aioredis.Redis:
    return aioredis.from_url(
        settings.redis_url,
        decode_responses=True,
        retry_on_timeout=True,  # переподключается при обрыве
        socket_keepalive=True,  # держит соединение живым при простое
    )


async def get_redis() -> aioredis.Redis:
    """Ленивое подключение. Один клиент на процесс."""
    global _client
    _client = _client or _make_client()
    return _client


async def close_redis() -> None:
    """Закрыть клиент при graceful shutdown."""
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None
        logger.debug("Redis client closed")