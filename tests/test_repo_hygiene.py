import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
COMPOSE = ROOT / "docker-compose.yml"
PYTHON_DOCKERFILE = ROOT / "docker" / "python.Dockerfile"
WEB = ROOT / "apps" / "web"
DIGEST = re.compile(r"@sha256:[0-9a-f]{64}$")


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _compose_images() -> list[str]:
    return re.findall(r"^\s*image:\s*(\S+)", _read(COMPOSE), re.MULTILINE)


def _dockerfile_bases() -> list[str]:
    return re.findall(r"^FROM\s+(\S+)", _read(PYTHON_DOCKERFILE), re.MULTILINE)


def _web_package() -> dict[str, Any]:
    package: dict[str, Any] = json.loads(_read(WEB / "package.json"))
    return package


def test_every_image_is_pinned_by_digest() -> None:
    images = _compose_images() + _dockerfile_bases()
    assert len(images) >= 5
    assert [image for image in images if not DIGEST.search(image)] == []


def test_python_services_build_from_shared_dockerfile() -> None:
    assert _read(COMPOSE).count("dockerfile: docker/python.Dockerfile") == 2
    assert not any(image.startswith("python:") for image in _compose_images())


def test_python_image_runs_as_non_root() -> None:
    users = re.findall(r"^USER\s+(\S+)", _read(PYTHON_DOCKERFILE), re.MULTILINE)
    assert users, "python.Dockerfile must set USER"
    assert users[-1].split(":")[0] not in {"root", "0"}


def test_python_image_installs_from_lockfile() -> None:
    assert "uv sync --frozen" in _read(PYTHON_DOCKERFILE)


def test_build_context_excludes_secrets_and_host_environments() -> None:
    ignored = set(_read(ROOT / ".dockerignore").split())
    assert {".env", ".git", ".venv", "**/node_modules"} <= ignored


def test_web_uses_pnpm_only() -> None:
    assert (WEB / "pnpm-lock.yaml").exists()
    assert not (WEB / "package-lock.json").exists()
    assert not (WEB / "yarn.lock").exists()
    assert _web_package()["packageManager"].startswith("pnpm@")
    assert not re.search(r"\bnpm\s+(install|ci)\b", _read(COMPOSE))
    assert "pnpm install --frozen-lockfile" in _read(COMPOSE)


def test_web_declares_xyflow_react() -> None:
    assert "@xyflow/react" in _web_package()["dependencies"]


def test_makefile_uses_uv_from_path() -> None:
    assert "~/.local/bin/uv" not in _read(ROOT / "Makefile")
