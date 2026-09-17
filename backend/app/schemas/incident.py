from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


Severity = Literal["low", "medium", "high", "critical"]
IncidentStatus = Literal["open", "investigating", "resolved"]


class IncidentCreate(BaseModel):
    service: str = Field(min_length=1, max_length=100)
    severity: Severity
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1)


class IncidentUpdate(BaseModel):
    status: IncidentStatus


class IncidentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    service: str
    severity: Severity
    status: IncidentStatus
    title: str
    description: str
    created_at: datetime
    updated_at: datetime


class IncidentListResponse(BaseModel):
    items: list[IncidentResponse]
    page: int
    page_size: int
    total: int
