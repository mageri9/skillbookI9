"""
Слой 1: сырые данные от GitHub API.
Ровно те поля, которые реально используются в collector.py.
"""

from datetime import datetime
from pydantic import BaseModel, Field


class FileChange(BaseModel):
    """Один изменённый файл в коммите"""

    filename: str
    additions: int = 0
    deletions: int = 0


class Commit(BaseModel):
    """Один коммит — 7-символьный хеш, дата, сообщение, файлы"""

    hash: str = Field(min_length=7, max_length=7)
    date: datetime
    message: str
    files: list[FileChange] = []


class RepoCommits(BaseModel):
    """Результат обработки одного репозитория"""

    repo: str
    period: str
    commits: list[Commit] = []