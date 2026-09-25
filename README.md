# multi-tenant-_agent_platform_telemetry_console

## Dependency choices
- `fastapi`/`uvicorn`: async API server for `apps/api`.
- `redis`: async Redis client for API and worker health/readiness checks.
- `pydantic`: strict schema/config models (`extra="forbid"`).
- `pytest`, `pytest-asyncio`, `httpx`: async endpoint testing without a live Redis instance.
- `ruff`: lightweight formatter for `make fmt`.
