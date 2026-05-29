#!/usr/bin/env python3
"""
Commit Chronicle — минимальный сборщик фактов
Никакой магии, только коммиты → JSON
"""

import json
import os
import sys
from datetime import datetime
from github import Github, Auth, GithubException, RateLimitExceededException
from dotenv import load_dotenv

load_dotenv()


def collect_commits(username: str, since_date: str) -> list[dict]:
    """Собирает коммиты пользователя без обработки"""

    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise ValueError("GITHUB_TOKEN not found")

    g = Github(auth=Auth.Token(token))

    # Проверяем лимиты
    try:
        rate_limit = g.get_rate_limit()
        remaining = rate_limit.core.remaining
        print(f"📡 API запросов осталось: {remaining}\n")
    except:
        pass

    user = g.get_user(username)
    repos = [r for r in user.get_repos() if not r.fork]
    print(f"📂 Найдено репозиториев: {len(repos)}\n")

    since = datetime.strptime(since_date, "%Y-%m-%d")
    all_manifests = []

    for i, repo in enumerate(repos, 1):
        print(f"[{i}/{len(repos)}] 📁 {repo.full_name}...", end=" ", flush=True)

        try:
            commits_manifest = []
            commits = repo.get_commits(author=username, since=since)

            for commit in commits:
                if len(commit.parents) > 1:
                    continue

                manifest = {
                    "hash": commit.sha[:7],
                    "date": commit.commit.author.date.isoformat(),
                    "message": commit.commit.message.split("\n")[0],
                    "files": {},
                }

                for file in commit.files or []:
                    manifest["files"][file.filename] = {
                        "+": file.additions or 0,
                        "-": file.deletions or 0,
                    }

                commits_manifest.append(manifest)

            if commits_manifest:
                all_manifests.append(
                    {
                        "repo": repo.full_name,
                        "period": f"{since_date}..{datetime.now().strftime('%Y-%m-%d')}",
                        "commits": commits_manifest,
                    }
                )
                print(f"✅ {len(commits_manifest)} коммитов")
            else:
                print("⏭️ нет коммитов")

        except RateLimitExceededException:
            print("❌ Лимит API исчерпан")
            break
        except GithubException as e:
            print(f"❌ GitHub API: {e.status} {e.data.get('message', '')}")
        except Exception as e:
            print(f"❌ {type(e).__name__}: {e}")

    return all_manifests


def main():
    username = os.getenv("GITHUB_USERNAME", "mageri9")
    since = os.getenv("GITHUB_SINCE", "2024-01-01")

    if len(sys.argv) > 1:
        username = sys.argv[1]
    if len(sys.argv) > 2:
        since = sys.argv[2]

    print(f"\n🚀 Commit Chronicle — сбор коммитов")
    print(f"👤 Пользователь: {username}")
    print(f"📅 Период: с {since}\n")

    manifests = collect_commits(username, since)

    output_file = "commit_chronicle.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(manifests, f, indent=2, ensure_ascii=False)

    total_commits = sum(len(m["commits"]) for m in manifests)

    print(f"\n{'=' * 50}")
    print(f"✅ Сохранено в {output_file}")
    print(f"📊 Репозиториев с коммитами: {len(manifests)}")
    print(f"📊 Всего коммитов: {total_commits}")


if __name__ == "__main__":
    main()