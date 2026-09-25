from typing import Protocol, Self, runtime_checkable

from pydantic import BaseModel, Field, JsonValue, model_validator

from contracts._types import ContractModel, SafeId


class ToolCall(ContractModel):
    id: str = Field(min_length=1, max_length=128)
    name: SafeId
    arguments: dict[str, JsonValue] = Field(default_factory=dict)


class ToolResult(ContractModel):
    call_id: str = Field(min_length=1, max_length=128)
    ok: bool
    output: dict[str, JsonValue] | None = None
    error: str | None = None

    @model_validator(mode="after")
    def _error_matches_ok(self) -> Self:
        if self.ok and self.error is not None:
            raise ValueError("error must be unset when ok is true")
        if not self.ok and not self.error:
            raise ValueError("error is required when ok is false")
        return self


@runtime_checkable
class Tool[InT: BaseModel, OutT: BaseModel](Protocol):
    @property
    def name(self) -> str: ...

    @property
    def description(self) -> str: ...

    @property
    def InputModel(self) -> type[InT]: ...

    @property
    def OutputModel(self) -> type[OutT]: ...

    @property
    def side_effecting(self) -> bool: ...

    async def run(self, args: InT) -> OutT: ...
