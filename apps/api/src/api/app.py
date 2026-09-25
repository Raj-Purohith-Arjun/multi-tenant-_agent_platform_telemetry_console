import os

from fastapi import Depends, FastAPI, HTTPException
from redis.asyncio import Redis, from_url

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
    if not await redis.ping():
        raise HTTPException(status_code=503, detail="redis unavailable")
    return HealthzResponse(status="ok", redis="ok")
