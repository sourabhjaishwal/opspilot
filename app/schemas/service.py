from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


ServiceStatus = Literal["healthy", "degraded", "down"]


class ServiceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=1000)
    status: ServiceStatus = "healthy"


class ServiceUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=1000)
    status: ServiceStatus | None = None


class ServiceStatusUpdate(BaseModel):
    status: ServiceStatus


class ServiceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    status: ServiceStatus
    last_checked_at: datetime | None
    created_at: datetime
    updated_at: datetime
