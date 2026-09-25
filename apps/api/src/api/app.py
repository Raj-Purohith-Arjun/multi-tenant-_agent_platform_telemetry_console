import os
from collections.abc import AsyncGenerator
from typing import Annotated

from contracts import HealthzResponse
from fastapi import Depends, FastAPI, Response
from redis.asyncio import Redis, from_url
from redis.exceptions import RedisError

from api.config import ApiSettings

app = FastAPI(title="multi-tenant-api")


async def get_redis() -> AsyncGenerator[Redis, None]:
    settings = ApiSettings(redis_url=os.getenv("REDIS_URL", "redis://localhost:6379/0"))
    redis = from_url(settings.redis_url, decode_responses=True)
    try:
        yield redis
    finally:
        await redis.aclose()


@app.get("/healthz", response_model=HealthzResponse)
async def healthz(
    response: Response, redis: Annotated[Redis, Depends(get_redis)]
) -> HealthzResponse:
    try:
        redis_ok = await redis.ping()
    except (RedisError, RuntimeError):
        redis_ok = False

    if not redis_ok:
        response.status_code = 503
        return HealthzResponse(status="degraded", redis="down")
    return HealthzResponse(status="ok", redis="ok")
