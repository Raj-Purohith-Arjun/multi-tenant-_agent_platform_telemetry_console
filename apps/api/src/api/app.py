import os

from fastapi import Depends, FastAPI
from fastapi.responses import JSONResponse
from redis.asyncio import Redis, from_url
from redis.exceptions import RedisError

from contracts import HealthzResponse

from api.config import ApiSettings

app = FastAPI(title="multi-tenant-api")


async def get_redis() -> Redis:
    settings = ApiSettings(redis_url=os.getenv("REDIS_URL", "redis://localhost:6379/0"))
    redis = from_url(settings.redis_url, decode_responses=True)
    try:
        yield redis
    finally:
        await redis.aclose()


@app.get("/healthz", response_model=HealthzResponse)
async def healthz(redis: Redis = Depends(get_redis)) -> HealthzResponse:
    try:
        redis_ok = await redis.ping()
    except (RedisError, RuntimeError):
        redis_ok = False

    if not redis_ok:
        return JSONResponse(
            status_code=503,
            content=HealthzResponse(status="degraded", redis="down").model_dump(),
        )
    return HealthzResponse(status="ok", redis="ok")
