FROM ghcr.io/astral-sh/uv:0.12.19@sha256:04d046b13e60d6bcec73cbc5e1cad25d680dea90c8573340950a0ac2d1aef424 AS uv

FROM python:3.12-slim@sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9

COPY --from=uv /uv /usr/local/bin/uv

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

ARG PACKAGE
WORKDIR /app

COPY pyproject.toml uv.lock ./
COPY packages/contracts packages/contracts
COPY apps/api apps/api
COPY apps/worker apps/worker
COPY apps/sandbox apps/sandbox

RUN uv sync --frozen --no-dev --no-editable --package "${PACKAGE}"

RUN useradd --system --uid 10001 --no-create-home app
USER 10001:10001
