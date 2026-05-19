import os
import csv
import re
import math
import json
import fnmatch
import sys
from datetime import datetime, date
from collections import defaultdict

from github import Github, Auth

from dotenv import load_dotenv


load_dotenv()

TOKEN = os.getenv("GITHUB_TOKEN")
USERNAME = os.getenv("GITHUB_USERNAME")
SINCE_DATE = os.getenv("SINCE_DATE", "2023-01-01")

MAX_LINES_FOR_WEIGHT = 300

if not TOKEN:
    raise ValueError("GITHUB_TOKEN not found in .env")


# ═══════════════════════════════════════════════
# ТАКСОНОМИЯ НАВЫКОВ
# ═══════════════════════════════════════════════
SKILL_RULES = {
    "paths": [
        ("*.py", "python", 0.9, "language"),
        ("*.ts", "typescript", 0.9, "language"),
        ("*.tsx", "react", 0.7, "frontend"),
        ("*.go", "go", 0.9, "language"),
        ("*.rs", "rust", 0.9, "language"),
        ("*.java", "java", 0.9, "language"),
        ("Dockerfile", "docker", 1.0, "devops"),
        ("docker-compose*.yml", "docker", 0.9, "devops"),
        (".github/workflows/*.yml", "ci/cd", 0.9, "devops"),
        ("*.tf", "terraform", 1.0, "infrastructure"),
        ("*.sql", "sql", 0.8, "database"),
        ("requirements.txt", "pip", 0.8, "python"),
        ("pyproject.toml", "pip", 0.8, "python"),
        ("package.json", "npm", 0.8, "javascript"),
        ("Makefile", "make", 0.8, "devops"),
        ("**/tests/**", "testing", 0.8, "testing"),
        ("**/test/**", "testing", 0.8, "testing"),
        ("**/migrations/**", "migrations", 0.9, "database"),
    ],
    "patches": [
        (r"FastAPI\(", "fastapi", 3, "backend"),
        (r"async\s+def\s", "asyncio", 2, "python"),
        (r"import\s+pytest|from\s+pytest", "pytest", 2, "testing"),
        (r"def\s+test_|class\s+Test", "testing", 3, "testing"),
        (r"SELECT\s.*FROM|INSERT\s+INTO|UPDATE\s.*SET", "sql", 2, "database"),
        (r"useState\(|useEffect\(|useCallback\(", "react-hooks", 3, "frontend"),
        (r"docker\s+build|docker\s+run|docker-compose", "docker", 2, "devops"),
        (r"@app\.route|@router\.|APIRouter", "fastapi", 3, "backend"),
        (r"class\s+\w+\(Base\)|session\.query|session\.add", "sqlalchemy", 3, "orm"),
        (r"import\s+pandas|from\s+pandas", "pandas", 3, "data"),
        (r"import\s+numpy|from\s+numpy", "numpy", 3, "data"),
        (r"matplotlib|plotly|seaborn", "visualization", 2, "data"),
        (r"pytest\.mark|@pytest\.fixture", "pytest", 2, "testing"),
        (r"unittest\.", "unittest", 2, "testing"),
        (r"@dataclass|from\s+dataclasses", "dataclasses", 1, "python"),
        (r"pydantic", "pydantic", 3, "python"),
        (r"celery|@task\b", "celery", 3, "backend"),
        (r"redis\.|Redis\(", "redis", 3, "database"),
        (r"kafka|KafkaConsumer|KafkaProducer", "kafka", 3, "backend"),
    ],
}

COMMIT_TYPE_PATTERNS = [
    (r"^feat[(:]", "feature"),
    (r"^fix[(:]", "bugfix"),
    (r"^refactor[(:]", "refactor"),
    (r"^test[(:]", "testing"),
    (r"^docs[(:]", "docs"),
    (r"^chore[(:]", "maintenance"),
    (r"^style[(:]", "style"),
    (r"^perf[(:]", "performance"),
]

IGNORE_GLOBS = [
    "README*", "*.md", ".gitignore", ".editorconfig",
    "LICENSE", "CHANGELOG*",
    "package-lock.json", "yarn.lock", "poetry.lock",
    "Pipfile.lock", "*.min.js", "*.min.css",
    "*.svg", "*.png", "*.jpg", "*.ico", "*.gif",
]

DIR_SEMANTICS = [
    ("/api/", "api-layer"),
    ("/core/", "core-architecture"),
    ("/infra/", "infrastructure"),
    ("/ml/", "machine-learning"),
    ("/models/", "data-modeling"),
    ("/utils/", "utilities"),
    ("/scripts/", "automation"),
    ("/handlers/", "event-handling"),
    ("/middleware/", "middleware"),
    ("/routes/", "routing"),
    ("/services/", "service-layer"),
    ("/repositories/", "data-access"),
]


# ═══════════════════════════════════════════════
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ═══════════════════════════════════════════════

def match_glob(filepath, pattern):
    """Glob с поддержкой **"""
    if "**" in pattern:
        prefix, suffix = pattern.split("**", 1)
        return filepath.startswith(prefix.rstrip("/")) and filepath.endswith(suffix.lstrip("/"))
    return fnmatch.fnmatch(filepath, pattern)


def classify_commit(message):
    """Тип коммита по сообщению"""
    for pattern, ctype in COMMIT_TYPE_PATTERNS:
        if re.search(pattern, message, re.IGNORECASE):
            return ctype
    return "other"


def extract_dir_semantics(filepath):
    """Семантика из пути директории"""
    return {meaning for pattern, meaning in DIR_SEMANTICS if pattern in filepath}


def extract_skills_from_file(file_info):
    """
    Из одного файла коммита извлекает список навыков.
    Возвращает: [(skill, confidence, category, patch_weight, semantics), ...]
    """
    path = file_info.filename
    patch = file_info.patch or ""
    has_patch = bool(file_info.patch)

    if any(match_glob(path, g) for g in IGNORE_GLOBS):
        return []

    results = []

    # Path-based
    for glob, skill, confidence, category in SKILL_RULES["paths"]:
        if match_glob(path, glob):
            results.append((skill, confidence, category, 0, set()))

    # Patch-based
    if has_patch:
        for regex, skill, boost, category in SKILL_RULES["patches"]:
            if re.search(regex, patch, re.IGNORECASE | re.MULTILINE):
                existing = [r for r in results if r[0] == skill]
                if existing:
                    idx = results.index(existing[0])
                    old = results[idx]
                    results[idx] = (old[0], min(1.0, old[1] + 0.2), old[2], old[3] + boost, old[4])
                else:
                    results.append((skill, 0.6, category, boost, set()))

    # Семантика директорий
    dir_sem = extract_dir_semantics(path)
    if dir_sem:
        results = [(s, c, cat, pw, sem | dir_sem) for s, c, cat, pw, sem in results]

    return results


def is_merge_commit(commit):
    return len(commit.parents) > 1


def compute_weight(changes, confidence, patch_weight):
    capped = min(changes, MAX_LINES_FOR_WEIGHT)
    base = math.log1p(capped)
    return round((base + patch_weight) * confidence, 2)


def recency_factor(commit_date_str, half_life_days=365):
    """Экспоненциальное затухание: 1 день → ~1.0, 365 дней → ~0.37"""
    days_ago = (date.today() - datetime.strptime(commit_date_str, "%Y-%m-%d").date()).days
    return math.exp(-days_ago / half_life_days)


# ═══════════════════════════════════════════════
# СБОР КОММИТОВ
# ═══════════════════════════════════════════════

def collect_commits(g, username, repos, since_date):
    since = datetime.strptime(since_date, "%Y-%m-%d")
    results = []

    for repo_name in repos:
        repo_full = f"{username}/{repo_name}"
        print(f"  Обрабатываю {repo_full}...")

        try:
            repo = g.get_repo(repo_full)
            commits = repo.get_commits(author=username, since=since)

            for commit in commits:
                if is_merge_commit(commit):
                    continue

                try:
                    files = commit.files
                except Exception:
                    continue

                commit_type = classify_commit(commit.commit.message)
                commit_date = commit.commit.author.date.strftime("%Y-%m-%d")
                sha = commit.sha[:7]
                message = commit.commit.message.split("\n")[0][:120]

                for file in files:
                    if not file.filename:
                        continue

                    additions = file.additions or 0
                    deletions = file.deletions or 0
                    changes = additions + deletions

                    if changes > 10000:
                        continue

                    skills = extract_skills_from_file(file)

                    for skill, confidence, category, patch_weight, semantics in skills:
                        weight = compute_weight(changes, confidence, patch_weight)
                        extension = os.path.splitext(file.filename)[1] or "no-ext"

                        results.append({
                            "date": commit_date,
                            "repo": repo_name,
                            "sha": sha,
                            "commit_type": commit_type,
                            "file": file.filename,
                            "extension": extension,
                            "skill": skill,
                            "category": category,
                            "confidence": round(confidence, 2),
                            "additions": additions,
                            "deletions": deletions,
                            "changes": changes,
                            "weight": weight,
                            "patch_available": bool(file.patch),
                            "semantics": "|".join(sorted(semantics)) if semantics else "",
                            "message": message,
                        })

        except Exception as e:
            print(f"    Ошибка: {e}")
            continue

    return results


# ═══════════════════════════════════════════════
# АГРЕГАЦИЯ И ВЫВОД
# ═══════════════════════════════════════════════

def save_to_csv(results, filename="skills.csv"):
    if not results:
        print("Нет данных для сохранения")
        return

    fields = [
        "date", "repo", "sha", "commit_type",
        "file", "extension", "skill", "category",
        "confidence", "additions", "deletions", "changes",
        "weight", "patch_available", "semantics", "message",
    ]

    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(results)

    print(f"  Сохранено {len(results)} записей в {filename}")


def build_cooccurrence(results):
    """Какие навыки встречаются в одних коммитах"""
    commit_skills = defaultdict(set)
    for r in results:
        commit_skills[r["sha"]].add(r["skill"])

    cooc = defaultdict(lambda: defaultdict(int))
    for skills in commit_skills.values():
        for s1 in skills:
            for s2 in skills:
                if s1 < s2:
                    cooc[s1][s2] += 1
                    cooc[s2][s1] += 1
    return cooc


def build_profile(results):
    """Агрегированный профиль с recency decay"""
    profile = defaultdict(lambda: {
        "unique_commits": set(),
        "repos": set(),
        "total_lines": 0,
        "total_weight": 0.0,
        "recency_weight": 0.0,
        "commit_types": defaultdict(int),
        "first_used": None,
        "last_used": None,
        "category": "",
        "monthly_activity": defaultdict(float),
    })

    for r in results:
        skill = r["skill"]
        p = profile[skill]

        p["unique_commits"].add(r["sha"])
        p["repos"].add(r["repo"])
        p["total_lines"] += r["changes"]
        p["total_weight"] += r["weight"]

        rf = recency_factor(r["date"])
        p["recency_weight"] += r["weight"] * rf

        p["commit_types"][r["commit_type"]] += 1

        if p["first_used"] is None or r["date"] < p["first_used"]:
            p["first_used"] = r["date"]
        if p["last_used"] is None or r["date"] > p["last_used"]:
            p["last_used"] = r["date"]

        p["category"] = r["category"]

        month = r["date"][:7]
        p["monthly_activity"][month] += r["weight"] * rf

    return profile


def print_profile(results):
    if not results:
        return

    profile = build_profile(results)
    cooc = build_cooccurrence(results)

    print()
    print("=" * 70)
    print("ИНЖЕНЕРНЫЙ ПРОФИЛЬ")
    print("=" * 70)

    sorted_skills = sorted(
        profile.items(),
        key=lambda x: x[1]["recency_weight"],
        reverse=True
    )

    for skill, data in sorted_skills[:20]:
        commits_count = len(data["unique_commits"])
        repos_count = len(data["repos"])

        types_str = ", ".join(
            f"{t}:{c}" for t, c in sorted(
                data["commit_types"].items(),
                key=lambda x: x[1], reverse=True
            )[:3]
        )

        last_date = datetime.strptime(data["last_used"], "%Y-%m-%d").date()
        days_since = (date.today() - last_date).days
        if days_since <= 30:
            status = "🟢 active"
        elif days_since <= 180:
            status = "🟡 stale"
        else:
            status = "⚪ declining"

        print(f"\n{skill} ({data['category']}) {status}")
        print(f"  Коммитов: {commits_count}  |  Репозиториев: {repos_count}")
        print(f"  Строк изменено: {data['total_lines']}")
        print(f"  Вес сырой: {data['total_weight']:.1f}  →  с recency: {data['recency_weight']:.1f}")
        print(f"  Типы: {types_str}")
        print(f"  Период: {data['first_used']} → {data['last_used']}")

        if skill in cooc:
            top_cooc = sorted(cooc[skill].items(), key=lambda x: x[1], reverse=True)[:5]
            cooc_str = ", ".join(f"{s}({c})" for s, c in top_cooc if c > 1)
            if cooc_str:
                print(f"  Вместе с: {cooc_str}")

    # JSON
    json_profile = {}
    for skill, data in profile.items():
        json_profile[skill] = {
            "category": data["category"],
            "unique_commits": len(data["unique_commits"]),
            "repos": sorted(data["repos"]),
            "total_lines": data["total_lines"],
            "raw_weight": round(data["total_weight"], 1),
            "recency_weight": round(data["recency_weight"], 1),
            "first_used": data["first_used"],
            "last_used": data["last_used"],
            "status": "active" if (date.today() - datetime.strptime(data["last_used"], "%Y-%m-%d").date()).days <= 30 else (
                "stale" if (date.today() - datetime.strptime(data["last_used"], "%Y-%m-%d").date()).days <= 180 else "declining"
            ),
            "commit_types": dict(data["commit_types"]),
            "monthly_activity": dict(sorted(data["monthly_activity"].items())),
        }

    json_cooc = {}
    for s1 in cooc:
        filtered = {s2: c for s2, c in cooc[s1].items() if c >= 2}
        if filtered:
            json_cooc[s1] = dict(sorted(filtered.items(), key=lambda x: x[1], reverse=True))

    with open("profile.json", "w", encoding="utf-8") as f:
        json.dump({"skills": json_profile, "cooccurrence": json_cooc}, f, indent=2, ensure_ascii=False)

    print(f"\n📄 profile.json сохранён")


# ═══════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════

if __name__ == "__main__":
    # CLI: python skillbok.py username
    if len(sys.argv) > 1:
        USERNAME = sys.argv[1]

    auth = Auth.Token(TOKEN)
    g = Github(auth=auth)
    user = g.get_user(USERNAME)
    repos = [repo.name for repo in user.get_repos()]

    print(f"Пользователь: {USERNAME}")
    print(f"Репозиториев: {len(repos)}")
    print(f"Первые 10: {repos[:10]}")
    print()

    results = collect_commits(g, USERNAME, repos, SINCE_DATE)
    save_to_csv(results)
    print_profile(results)