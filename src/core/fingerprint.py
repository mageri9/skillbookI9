"""Fingerprint текущего состояния GitHub пользователя."""

import hashlib
from src.core.token_rotator import token_rotator


def get_github_fingerprint(username: str) -> str:
    """
    Отпечаток состояния GitHub: repo:pushed_at для всех репо.
    Используется при сохранении и при проверке свежести кеша.
    """
    g = token_rotator.get_client()

    try:
        user = g.get_user(username)
        repos = list(user.get_repos(type="owner"))[:100]  # защита от 800 репо
    except Exception:
        return ""

    data = []
    for repo in repos:
        if repo.fork:
            continue
        pushed = repo.pushed_at.isoformat() if repo.pushed_at else "none"
        data.append(f"{repo.full_name}:{pushed}")

    data.sort()
    raw = "|".join(data)

    return hashlib.sha256(raw.encode()).hexdigest()