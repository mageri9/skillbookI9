"""
Единые Pydantic-модели на весь проект.
Используются collector'ом, кешем, LLM — без лишних слоёв.
"""

from datetime import datetime
from pydantic import BaseModel, Field


class FileChange(BaseModel):
    """Один изменённый файл в коммите"""

    filename: str
    additions: int = 0
    deletions: int = 0


class Commit(BaseModel):
    """Один коммит со всеми данными"""

    hash: str
    date: datetime
    message: str
    repo: str
    files: list[FileChange] = Field(default_factory=list)


class AnalysisResult(BaseModel):
    """Полный результат анализа — то что collector отдаёт наружу"""

    username: str
    period: str
    commits: list[Commit]
    generated_at: datetime = datetime.now()


class CompactFile(BaseModel):
    p: str
    plus: int | None = None
    minus: int | None = None

    @property
    def add(self) -> int:
        return self.plus or 0

    @property
    def delete(self) -> int:
        return self.minus or 0


class CompactCommit(BaseModel):
    dt: str
    msg: str
    f: list[CompactFile] = []


class CompactResult(BaseModel):
    user: str
    period: str
    repos: dict[str, list[CompactCommit]]