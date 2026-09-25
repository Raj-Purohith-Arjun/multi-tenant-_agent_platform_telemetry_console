import json
from pathlib import Path

from pydantic import TypeAdapter

from contracts.enums import HaltReason, RunStatus
from contracts.events import Event
from contracts.health import HealthzResponse
from contracts.run import RunConfig, RunState
from contracts.tools import ToolCall, ToolResult

SCHEMA_DIR = Path(__file__).resolve().parents[2] / "schemas"

SCHEMA_TYPES: dict[str, type] = {
    "event.json": Event,
    "halt_reason.json": HaltReason,
    "healthz_response.json": HealthzResponse,
    "run_config.json": RunConfig,
    "run_state.json": RunState,
    "run_status.json": RunStatus,
    "tool_call.json": ToolCall,
    "tool_result.json": ToolResult,
}


def render_schemas() -> dict[str, str]:
    return {
        name: json.dumps(TypeAdapter(tp).json_schema(), indent=2, sort_keys=True) + "\n"
        for name, tp in sorted(SCHEMA_TYPES.items())
    }


def write_schemas(directory: Path = SCHEMA_DIR) -> list[Path]:
    rendered = render_schemas()
    directory.mkdir(parents=True, exist_ok=True)
    for stale in directory.glob("*.json"):
        if stale.name not in rendered:
            stale.unlink()
    written = []
    for name, text in rendered.items():
        path = directory / name
        path.write_text(text, encoding="utf-8", newline="\n")
        written.append(path)
    return written


def main() -> None:
    for path in write_schemas():
        print(path)


if __name__ == "__main__":
    main()
