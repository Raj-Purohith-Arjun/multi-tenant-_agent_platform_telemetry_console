from collections.abc import AsyncGenerator

import pytest
from api.app import app, get_redis
from httpx import ASGITransport, AsyncClient


class RedisStub:
    def __init__(
        self, ping_result: bool = True, ping_exception: Exception | None = None
    ) -> None:
        self.ping_result = ping_result
        self.ping_exception = ping_exception

    async def ping(self) -> bool:
        if self.ping_exception is not None:
            raise self.ping_exception
        return self.ping_result


@pytest.mark.asyncio
async def test_healthz_returns_ok_when_redis_ping_succeeds() -> None:
    async def override_redis() -> AsyncGenerator[RedisStub, None]:
        yield RedisStub(ping_result=True)

    app.dependency_overrides[get_redis] = override_redis
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/healthz")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "redis": "ok"}


@pytest.mark.asyncio
async def test_healthz_returns_503_when_redis_ping_fails() -> None:
    async def override_redis() -> AsyncGenerator[RedisStub, None]:
        yield RedisStub(ping_result=False)

    app.dependency_overrides[get_redis] = override_redis
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/healthz")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503
    assert response.json() == {"status": "degraded", "redis": "down"}


@pytest.mark.asyncio
async def test_healthz_returns_503_when_redis_ping_raises_runtime_error() -> None:
    async def override_redis() -> AsyncGenerator[RedisStub, None]:
        yield RedisStub(ping_exception=RuntimeError("redis unavailable"))

    app.dependency_overrides[get_redis] = override_redis
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/healthz")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503
    assert response.json() == {"status": "degraded", "redis": "down"}
