from pydantic import Field, JsonValue, NonNegativeInt

from contracts._types import ContractModel, SafeId, UtcDatetime, utc_now
from contracts.enums import EventType


class Event(ContractModel):
    seq: NonNegativeInt
    run_id: SafeId
    tenant_id: SafeId
    type: EventType
    ts: UtcDatetime = Field(default_factory=utc_now)
    payload: dict[str, JsonValue] = Field(default_factory=dict)
