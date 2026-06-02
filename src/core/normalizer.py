"""Конвертация сырых данных collector'а в Pydantic-модели."""

from datetime import datetime
from src.models.models import AnalysisResult, Commit, FileChange


def normalize(raw_data: list[dict], username: str) -> AnalysisResult:
    """
    raw_data: список словарей от process_single_repo
    username: GitHub-логин
    возвращает: валидированный AnalysisResult
    """
    all_commits: list[Commit] = []
    period = ""

    for repo_data in raw_data:
        period = repo_data.get("period", "")
        repo_name = repo_data.get("repo", "")

        for c in repo_data.get("commits", []):
            commit = Commit(
                hash=c["hash"],
                date=datetime.fromisoformat(c["date"]),
                message=c["message"],
                repo=repo_name,
                files=[
                    FileChange(
                        filename=name,
                        additions=ch.get("+", 0),
                        deletions=ch.get("-", 0),
                    )
                    for name, ch in c.get("files", {}).items()
                ],
            )
            all_commits.append(commit)

    return AnalysisResult(
        username=username,
        period=period,
        commits=all_commits,
        generated_at=datetime.now(),
    )