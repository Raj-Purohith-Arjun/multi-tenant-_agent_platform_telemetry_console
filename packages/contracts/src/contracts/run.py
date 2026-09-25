from typing import Self

from pydantic import Field, NonNegativeInt, PositiveInt, model_validator

from contracts._types import ContractModel, SafeId, UtcDatetime, utc_now
from contracts.enums import HaltReason, RunStatus

_NO_HALT_REASON = {RunStatus.QUEUED, RunStatus.RUNNING, RunStatus.SUCCEEDED}


class RunConfig(ContractModel):
    max_steps: PositiveInt = 20
    max_wall_clock_s: PositiveInt = 120
    max_tokens: PositiveInt = 50000
    loop_window: PositiveInt = 6
    loop_repeat_threshold: int = Field(default=3, ge=2)

    @model_validator(mode="after")
    def _threshold_fits_window(self) -> Self:
        if self.loop_repeat_threshold > self.loop_window:
            raise ValueError("loop_repeat_threshold must not exceed loop_window")
        return self


class RunState(ContractModel):
    run_id: SafeId
    tenant_id: SafeId
    status: RunStatus = RunStatus.QUEUED
    halt_reason: HaltReason | None = None
    version: NonNegativeInt = 0
    step: NonNegativeInt = 0
    tokens_used: NonNegativeInt = 0
    config: RunConfig = Field(default_factory=RunConfig)
    created_at: UtcDatetime = Field(default_factory=utc_now)
    updated_at: UtcDatetime = Field(default_factory=utc_now)

    @model_validator(mode="after")
    def _halt_reason_matches_status(self) -> Self:
        if self.status is RunStatus.HALTED and self.halt_reason is None:
            raise ValueError("halt_reason is required when status is halted")
        if self.status in _NO_HALT_REASON and self.halt_reason is not None:
            raise ValueError(f"halt_reason must be unset when status is {self.status}")
        return self
