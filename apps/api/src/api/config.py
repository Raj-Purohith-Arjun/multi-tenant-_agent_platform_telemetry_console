from pydantic import BaseModel, ConfigDict


class ApiSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")

    redis_url: str = "redis://localhost:6379/0"
