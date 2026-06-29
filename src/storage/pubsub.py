"""Redis pub/sub — publish и subscribe."""

from redis.asyncio.client import PubSub

from src.logger import get_logger
from src.storage.redis import get_redis

logger = get_logger(__name__)


async def publish(channel: str, message: str) -> None:
    """Опубликовать сообщение в канал.

    Пробрасывает исключение наружу — вызывающий код (tasks.py)
    решает как реагировать на недоступность Redis.
    """
    client = await get_redis()
    try:
        await client.publish(channel, message)
        logger.debug(f"publish → {channel!r}: {message!r}")
    except Exception as e:
        logger.error(f"publish({channel!r}) failed: {e}")
        raise


async def subscribe(channel: str):
    """Подписаться на канал. Async generator — отдаёт данные сообщений.

    Использует отдельный pubsub-объект поверх общего клиента —
    SUBSCRIBE блокирует соединение на listen, поэтому pubsub
    работает на выделенном соединении из пула, не мешая GET/SET/PUBLISH.

    Гарантирует unsubscribe + aclose при любом выходе (break / исключение).
    При ошибке во время listen — пробрасывает исключение наружу,
    чтобы bot listener мог применить retry-логику.
    """
    client = await get_redis()
    pubsub: PubSub = client.pubsub()
    await pubsub.subscribe(channel)
    logger.debug(f"subscribe → {channel!r}")

    try:
        async for msg in pubsub.listen():
            logger.debug(f"pubsub {msg['type']} ← {channel!r}: {msg.get('data')!r}")
            if msg["type"] == "message":
                yield msg["data"]
    except Exception as e:
        logger.error(f"subscribe({channel!r}) error: {e}")
        raise
    finally:
        await pubsub.unsubscribe(channel)
        await pubsub.aclose()
        logger.debug(f"unsubscribe ← {channel!r}")