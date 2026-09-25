from enum import StrEnum
from typing import Literal


class RunStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    HALTED = "halted"
    CANCELLED = "cancelled"


class HaltReason(StrEnum):
    MAX_STEPS = "max_steps"
    MAX_WALL_CLOCK = "max_wall_clock"
    MAX_TOKENS = "max_tokens"
    LOOP_DETECTED = "loop_detected"
    CANCELLED = "cancelled"
    ERROR = "error"


EventType = Literal[
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
]
