# Commit Chronicle

Минимальный сборщик коммитов с GitHub. Никакой магии — только факты в `JSON`.

## ✨ Возможности

- Сбор коммитов по пользователю и начальной дате
- Автоматический пропуск merge-коммитов
- Фиксация изменений по файлам (`+` / `-` строк)
- Проверка остатка API-запросов и graceful-обработка ошибок
- Конфигурация через `.env` или аргументы командной строки

## 📦 Установка

```bash
pip install PyGithub python-dotenv
```

Создайте `.env` (или экспортируйте переменные):

```env
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx
GITHUB_USERNAME=ваше имя
GITHUB_SINCE=2024-01-01
```

> 🔑 Токен должен иметь доступ к чтению репозиториев (`repo` или `public_repo`).

## 🚀 Использование

```bash
# С настройками из .env
python commit_chronicle.py

# С явными аргументами (перезаписывают .env)
python commit_chronicle.py <username> <YYYY-MM-DD>
```

Результат сохраняется в `commit_chronicle.json`. Прогресс и ошибки выводятся в консоль.

## 📄 Формат вывода

```json
[
  {
    "repo": "username/repo-name",
    "period": "2024-01-01..2026-05-29",
    "commits": [
      {
        "hash": "7d20522",
        "date": "2026-04-26T04:45:43+00:00",
        "message": "fix(backend): correct group name in Dockerfile",
        "files": {
          "backend/Dockerfile": {
            "+": 1,
            "-": 1
          }
        }
      }
    ]
  }
]
```

## ⚙️ Требования

- Python 3.10+
- `PyGithub`, `python-dotenv`
- Валидный `GITHUB_TOKEN`
- Сетевой доступ к `api.github.com`

## 📌 Примечание

Скрипт собирает только репозитории, принадлежащие пользователю (форки игнорируются), и фильтрует коммиты с более чем
одним родителем (merge). Лимиты API проверяются перед стартом; при исчерпании сбор останавливается с сообщением.