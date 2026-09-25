from datetime import UTC, datetime, timedelta, timezone
from typing import Any, get_args

import pytest
from contracts import (
    Event,
    EventType,
    HaltReason,
    HealthzResponse,
    RunConfig,
    RunState,
    RunStatus,
    ToolCall,
    ToolResult,
)
from pydantic import BaseModel, ValidationError

NOW = datetime(2026, 1, 2, 3, 4, 5, tzinfo=UTC)

EXPECTED_EVENT_TYPES = {
    "run.queued",
    "run.started",
    "step.started",
    "llm.request",
    "llm.response",
    "tool.call",
    "tool.result",
    "tool.error",
    "checkpoint.saved",
    "run.halted",
    "run.completed",
    "run.failed",
    "run.cancelled",
}


def sample_instances() -> list[BaseModel]:
    return [
        HealthzResponse(status="ok", redis="ok"),
        ToolCall(id="call_1", name="echo", arguments={"text": "hi", "n": [1, 2]}),
        ToolResult(call_id="call_1", ok=True, output={"text": "hi"}),
        ToolResult(call_id="call_2", ok=False, error="boom"),
        RunConfig(),
        RunState(
            run_id="run_1",
            tenant_id="acme",
            status=RunStatus.HALTED,
            halt_reason=HaltReason.MAX_STEPS,
            version=3,
            step=20,
            created_at=NOW,
            updated_at=NOW,
        ),
        Event(
            seq=0,
            run_id="run_1",
            tenant_id="acme",
            type="tool.call",
            ts=NOW,
            payload={"name": "echo"},
        ),
    ]


def valid_payload(model: type[BaseModel]) -> dict[str, Any]:
    for instance in sample_instances():
        if type(instance) is model:
            return instance.model_dump(mode="json")
    raise AssertionError(f"no sample for {model.__name__}")


ALL_MODELS = [HealthzResponse, ToolCall, ToolResult, RunConfig, RunState, Event]


@pytest.mark.parametrize("instance", sample_instances(), ids=lambda m: type(m).__name__)
def test_round_trip_through_json(instance: BaseModel) -> None:
    restored = type(instance).model_validate_json(instance.model_dump_json())
    assert restored == instance


@pytest.mark.parametrize("model", ALL_MODELS, ids=lambda m: m.__name__)
def test_every_model_forbids_extra_fields(model: type[BaseModel]) -> None:
    assert model.model_config.get("extra") == "forbid"
    payload = valid_payload(model) | {"unexpected": 1}
    with pytest.raises(ValidationError, match="extra_forbidden"):
        model.model_validate(payload)


def test_nested_run_config_forbids_extra_fields() -> None:
    payload = valid_payload(RunState)
    payload["config"]["surprise"] = True
    with pytest.raises(ValidationError, match="extra_forbidden"):
        RunState.model_validate(payload)


def test_run_config_defaults() -> None:
    config = RunConfig()
    assert config.max_steps == 20
    assert config.max_wall_clock_s == 120
    assert config.max_tokens == 50000
    assert config.loop_window == 6
    assert config.loop_repeat_threshold == 3


@pytest.mark.parametrize(
    "field", ["max_steps", "max_wall_clock_s", "max_tokens", "loop_window"]
)
def test_run_config_rejects_non_positive_limits(field: str) -> None:
    with pytest.raises(ValidationError):
        RunConfig.model_validate({field: 0})


def test_run_config_rejects_threshold_larger_than_window() -> None:
    with pytest.raises(ValidationError, match="loop_repeat_threshold"):
        RunConfig(loop_window=3, loop_repeat_threshold=4)


def test_event_type_is_closed_literal_of_13_types() -> None:
    assert set(get_args(EventType)) == EXPECTED_EVENT_TYPES
    assert len(get_args(EventType)) == 13


def test_event_rejects_unknown_type() -> None:
    payload = valid_payload(Event) | {"type": "tool.exploded"}
    with pytest.raises(ValidationError, match="literal_error"):
        Event.model_validate(payload)


def test_run_state_rejects_invalid_status() -> None:
    payload = valid_payload(RunState) | {"status": "paused"}
    with pytest.raises(ValidationError, match="enum"):
        RunState.model_validate(payload)


def test_run_state_rejects_invalid_halt_reason() -> None:
    payload = valid_payload(RunState) | {"halt_reason": "bored"}
    with pytest.raises(ValidationError, match="enum"):
        RunState.model_validate(payload)


def test_run_state_defaults_are_fresh_per_instance() -> None:
    a = RunState(run_id="run_a", tenant_id="acme")
    b = RunState(run_id="run_b", tenant_id="acme")
    assert a.status is RunStatus.QUEUED
    assert a.version == 0
    assert a.halt_reason is None
    assert a.config == RunConfig()
    assert a.config is not b.config


def test_run_state_rejects_negative_version() -> None:
    with pytest.raises(ValidationError):
        RunState(run_id="run_1", tenant_id="acme", version=-1)


def test_halted_run_requires_halt_reason() -> None:
    with pytest.raises(ValidationError, match="halt_reason"):
        RunState(run_id="run_1", tenant_id="acme", status=RunStatus.HALTED)


@pytest.mark.parametrize(
    "status", [RunStatus.QUEUED, RunStatus.RUNNING, RunStatus.SUCCEEDED]
)
def test_active_or_succeeded_run_rejects_halt_reason(status: RunStatus) -> None:
    with pytest.raises(ValidationError, match="halt_reason"):
        RunState(
            run_id="run_1",
            tenant_id="acme",
            status=status,
            halt_reason=HaltReason.ERROR,
        )


@pytest.mark.parametrize("tenant_id", ["", "acme:evil", "a b", "x" * 65, "t:*"])
def test_tenant_id_must_be_safe_for_redis_key_prefix(tenant_id: str) -> None:
    with pytest.raises(ValidationError):
        RunState(run_id="run_1", tenant_id=tenant_id)
    with pytest.raises(ValidationError):
        Event(seq=0, run_id="run_1", tenant_id=tenant_id, type="run.started")


def test_naive_datetimes_are_rejected() -> None:
    naive = datetime(2026, 1, 2, 3, 4, 5)  # noqa: DTZ001
    with pytest.raises(ValidationError, match="timezone"):
        RunState(run_id="run_1", tenant_id="acme", created_at=naive)
    with pytest.raises(ValidationError, match="timezone"):
        Event(seq=0, run_id="run_1", tenant_id="acme", type="run.started", ts=naive)


def test_aware_datetimes_are_normalised_to_utc() -> None:
    ist = timezone(timedelta(hours=5, minutes=30))
    local = datetime(2026, 1, 2, 8, 34, 5, tzinfo=ist)
    state = RunState(run_id="run_1", tenant_id="acme", created_at=local)
    event = Event(seq=0, run_id="run_1", tenant_id="acme", type="run.started", ts=local)
    assert state.created_at == NOW
    assert state.created_at.utcoffset() == timedelta(0)
    assert event.ts.utcoffset() == timedelta(0)


def test_default_timestamps_are_utc() -> None:
    state = RunState(run_id="run_1", tenant_id="acme")
    event = Event(seq=0, run_id="run_1", tenant_id="acme", type="run.started")
    assert state.created_at.utcoffset() == timedelta(0)
    assert state.updated_at.utcoffset() == timedelta(0)
    assert event.ts.utcoffset() == timedelta(0)


def test_event_rejects_negative_seq() -> None:
    with pytest.raises(ValidationError):
        Event(seq=-1, run_id="run_1", tenant_id="acme", type="run.started")


def test_tool_call_arguments_default_is_fresh_per_instance() -> None:
    a = ToolCall(id="c1", name="echo")
    b = ToolCall(id="c2", name="echo")
    assert a.arguments == {}
    assert a.arguments is not b.arguments


def test_tool_call_rejects_non_json_arguments() -> None:
    with pytest.raises(ValidationError):
        ToolCall.model_validate(
            {"id": "c1", "name": "echo", "arguments": {"f": object()}}
        )


def test_failed_tool_result_requires_error() -> None:
    with pytest.raises(ValidationError, match="error"):
        ToolResult(call_id="c1", ok=False)


def test_successful_tool_result_rejects_error() -> None:
    with pytest.raises(ValidationError, match="error"):
        ToolResult(call_id="c1", ok=True, output={}, error="nope")
