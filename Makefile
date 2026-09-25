.PHONY: up down logs test fmt

up:
	docker compose up --build

down:
	docker compose down --remove-orphans

logs:
	docker compose logs -f

test:
	~/.local/bin/uv run --package api pytest apps/api/tests -q

fmt:
	~/.local/bin/uv run ruff format apps packages
