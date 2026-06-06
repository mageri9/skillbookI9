"""
Конфигурация arq-воркера.
"""

from src.worker.tasks import analyze_github_user
from src.config import settings
from src.storage.database import init_db


class WorkerSettings:
    functions = [analyze_github_user]
    redis_settings = settings.redis_url
    max_jobs = 3
    job_timeout = 300
    keep_result = 3600

    async def on_startup(self, ctx):
        await init_db()

    async def on_shutdown(self, ctx):
        pass