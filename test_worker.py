import asyncio
from arq import create_pool
from arq.connections import RedisSettings


async def test():
    pool = await create_pool(RedisSettings(host="localhost", port=6379, database=0))
    job = await pool.enqueue_job("analyze_github_user", "mageri9", "2024-01-01")
    print(f"Job ID: {job.job_id}")

    result = await job.result(timeout=120)
    print(f"Status: {result['status']}")
    if result.get("result_json"):
        print(f"Data: {len(result['result_json'])} chars")


asyncio.run(test())