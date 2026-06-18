"""Сравнение размеров и токенов: старый JSON vs компактный."""

import json
from src.models.models import AnalysisResult, serialize_result


def count_tokens(text: str, model: str = "gpt-4") -> int:
    """Подсчет токенов через tiktoken."""
    try:
        import tiktoken

        encoding = tiktoken.encoding_for_model(model)
        return len(encoding.encode(text))
    except ImportError:
        return -1


def benchmark() -> None:
    """Взять AnalysisResult из БД, сравнить форматы."""
    import asyncio
    from src.storage.database import engine, requests

    async def run() -> None:
        async with engine.connect() as conn:
            result = await conn.execute(
                requests.select()
                .where(requests.c.status == "done")
                .order_by(requests.c.created_at.desc())
                .limit(1)
            )
            row = result.first()

        if not row:
            print("❌ Нет завершённых запросов в БД")
            return

        record = dict(row._mapping)
        raw_json = record["result_json"]

        old_size = len(raw_json)

        try:
            data = AnalysisResult.model_validate_json(raw_json)
            compact_json = serialize_result(data)
        except Exception:
            old_data = json.loads(raw_json)
            print("⚠️  В БД уже компактный формат. Сравнение с самим собой.")
            compact_json = raw_json
            old_size = len(raw_json)

        new_size = len(compact_json)

        old_tokens = count_tokens(raw_json)
        new_tokens = count_tokens(compact_json)

        print(f"{'=' * 50}")
        print(f"📊 Сравнение форматов JSON")
        print(f"{'=' * 50}")
        print(f"{'':<15} {'Байт':>8} {'Токенов':>8}")
        print(f"{'Старый':<15} {old_size:>8} {old_tokens:>8}")
        print(f"{'Компактный':<15} {new_size:>8} {new_tokens:>8}")
        print(f"{'Экономия':<15} {100 - new_size / old_size * 100:>7.1f}%", end="")
        if old_tokens > 0:
            print(f" {100 - new_tokens / old_tokens * 100:>7.1f}%")
        else:
            print()
        print(f"{'=' * 50}")

        if old_tokens == -1:
            print("💡 Установи tiktoken: pip install tiktoken")

    asyncio.run(run())


    if __name__ == "__main__":
        benchmark()