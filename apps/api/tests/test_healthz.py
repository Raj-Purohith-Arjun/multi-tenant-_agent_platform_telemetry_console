import pytest
from httpx import ASGITransport, AsyncClient
from redis.exceptions import ConnectionError

from api.app import app, get_redis


class RedisStub:
    def __init__(self, ping_result: bool) -> None:
        self.ping_result = ping_result

    async def ping(self) -> bool:
        return self.ping_result


class FailingRedisStub:
    async def ping(self) -> bool:
        raise ConnectionError("redis down")


@pytest.mark.asyncio
async def test_healthz_returns_ok_when_redis_ping_succeeds() -> None:
    async def override_redis() -> RedisStub:
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
    async def override_redis() -> RedisStub:
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
    assert response.json() == {"status": "down", "redis": "down"}


@pytest.mark.asyncio
async def test_healthz_returns_503_when_redis_raises_connection_error() -> None:
    async def override_redis() -> FailingRedisStub:
        yield FailingRedisStub()

    app.dependency_overrides[get_redis] = override_redis
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/healthz")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503
    assert response.json() == {"status": "down", "redis": "down"}
