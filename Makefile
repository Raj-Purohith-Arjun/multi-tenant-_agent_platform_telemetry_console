.PHONY: up down logs test fmt

up:
	docker compose up --build

down:
	docker compose down --remove-orphans

logs:
	docker compose logs -f

test:
	uv run --package api pytest apps/api/tests -q

fmt:
	uv run ruff format apps packages
