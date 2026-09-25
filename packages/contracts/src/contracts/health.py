from pydantic import BaseModel, ConfigDict


class HealthzResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str
    redis: str
