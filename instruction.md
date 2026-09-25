# Project: Multi-Tenant Agent Platform & Telemetry Console

## Architecture (do not deviate)
- `apps/api`: FastAPI gateway (auth, tenancy, run CRUD, SSE). Python 3.12, uv, Pydantic v2.
- `apps/worker`: agent loop ("harness"). Holds LLM keys. NEVER executes untrusted code in-process.
- `apps/sandbox`: runner that executes untrusted code in throwaway Docker containers.
- `apps/web`: Next.js (App Router, TypeScript strict, Tailwind, `@xyflow/react`).
- `packages/contracts`: shared Pydantic models. Single source of truth for schemas.
- Redis 8 for checkpoints, leases, event streams, quotas, queues.

## Rules
- Every Redis key is prefixed `t:{tenant_id}:`. No exceptions.
- All tool inputs/outputs are Pydantic models with `model_config = ConfigDict(extra="forbid")`.
- Async everywhere in Python (`redis.asyncio`, `httpx.AsyncClient`).
- No secrets in the sandbox. Sandbox containers: `--network none`, read-only, non-root, resource-limited.
- Every new behavior ships with pytest tests. Never delete or weaken an existing test to make it pass.
- Use structured logging (JSON) with `run_id` and `tenant_id` on every line.
- Prefer small files (<300 lines). No new dependencies without stating why.
