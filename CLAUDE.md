# CLAUDE.md

@.github/copilot-instructions.md

## How to work in this repo
- Build plan: we are executing a 14-step plan. Steps 0-2 are done (scaffold + contracts). Do one step at a time.
- Before changing code for a step: restate the acceptance criteria, then write/adjust tests first.
- Commands:
  - Python tests: `uv run pytest -q`
  - Single package: `uv run pytest packages/contracts -q`
  - Lint/format: `uv run ruff check . && uv run ruff format --check .`
  - Types: `uv run mypy packages apps --ignore-missing-imports`
  - Stack: `docker compose up -d --build`, logs: `docker compose logs -f <svc>`
- Definition of done for any step: tests green, ruff clean, mypy clean, `docker compose up` healthy, no new deps without justification.
- Never weaken or delete a test to make it pass. Never run `git push` or `git commit` unless asked.
