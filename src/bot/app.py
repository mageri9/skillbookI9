"""Фабрика Telegram-приложения."""

from telegram.ext import Application
from arq import create_pool
from arq.connections import RedisSettings
from src.config import settings

_arq_pool = None


async def get_arq_pool():
    """Ленивое подключение к Redis для arq."""
    global _arq_pool
    if _arq_pool is None:
        _arq_pool = await create_pool(
            RedisSettings(host="localhost", port=6379, database=0)
        )
    return _arq_pool


def create_app() -> Application:
    """Создать и вернуть Application."""
    return Application.builder().token(settings.telegram_bot_token).build()