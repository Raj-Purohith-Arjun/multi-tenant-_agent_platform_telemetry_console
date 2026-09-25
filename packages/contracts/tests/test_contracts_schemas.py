import json
from pathlib import Path

from contracts.export_schemas import (
    SCHEMA_DIR,
    SCHEMA_TYPES,
    render_schemas,
    write_schemas,
)

MODEL_FILES = {
    "event.json",
    "healthz_response.json",
    "run_config.json",
    "run_state.json",
    "tool_call.json",
    "tool_result.json",
}
ENUM_FILES = {"halt_reason.json", "run_status.json"}
EXPECTED_FILES = MODEL_FILES | ENUM_FILES


def test_schema_set_covers_every_contract_type() -> None:
    assert set(render_schemas()) == EXPECTED_FILES
    assert len(SCHEMA_TYPES) == len(EXPECTED_FILES)


def test_rendering_is_deterministic() -> None:
    assert render_schemas() == render_schemas()


def test_write_schemas_creates_valid_json(tmp_path: Path) -> None:
    written = write_schemas(tmp_path)
    assert {p.name for p in written} == EXPECTED_FILES
    for path in written:
        schema = json.loads(path.read_text(encoding="utf-8"))
        assert path.read_bytes().endswith(b"}\n")
        if path.name in MODEL_FILES:
            assert schema["additionalProperties"] is False
        else:
            assert schema["type"] == "string"
            assert schema["enum"]


def test_write_schemas_removes_stale_files(tmp_path: Path) -> None:
    (tmp_path / "removed_model.json").write_text("{}\n", encoding="utf-8")
    write_schemas(tmp_path)
    assert {p.name for p in tmp_path.glob("*.json")} == EXPECTED_FILES


def test_event_schema_lists_all_13_types() -> None:
    schema = json.loads(render_schemas()["event.json"])
    assert len(schema["properties"]["type"]["enum"]) == 13


def test_enum_schemas_match_enum_values() -> None:
    run_status = json.loads(render_schemas()["run_status.json"])
    halt_reason = json.loads(render_schemas()["halt_reason.json"])
    assert run_status["enum"] == [
        "queued",
        "running",
        "succeeded",
        "failed",
        "halted",
        "cancelled",
    ]
    assert halt_reason["enum"] == [
        "max_steps",
        "max_wall_clock",
        "max_tokens",
        "loop_detected",
        "cancelled",
        "error",
    ]


def test_committed_schemas_match_models() -> None:
    rendered = render_schemas()
    committed = {
        p.name: p.read_text(encoding="utf-8") for p in SCHEMA_DIR.glob("*.json")
    }
    assert committed == rendered, (
        "Schemas are stale. Run: uv run python -m contracts.export_schemas"
    )
