import asyncio
import json
import os

from pydantic import BaseModel, ConfigDict
from redis.asyncio import from_url


class WorkerSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")

    redis_url: str = "redis://localhost:6379/0"
    run_id: str = "worker-bootstrap"
    tenant_id: str = "system"


def log_event(message: str, run_id: str, tenant_id: str) -> None:
    print(
        json.dumps(
            {
                "level": "info",
                "message": message,
                "run_id": run_id,
                "tenant_id": tenant_id,
            }
        ),
        flush=True,
    )


async def run() -> None:
    settings = WorkerSettings(
        redis_url=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
        run_id=os.getenv("RUN_ID", "worker-bootstrap"),
        tenant_id=os.getenv("TENANT_ID", "system"),
    )
    redis = from_url(settings.redis_url, decode_responses=True)
    try:
        await redis.ping()
        log_event("worker ready", run_id=settings.run_id, tenant_id=settings.tenant_id)
        await asyncio.Event().wait()
    finally:
        await redis.aclose()


def main() -> None:
    asyncio.run(run())
