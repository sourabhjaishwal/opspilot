from pydantic import BaseModel, Field


class AIIncidentAnalysis(BaseModel):
    summary: str = Field(
        description="A concise summary of the incident clearly stating this is an AI-generated recommendation."
    )
    possible_root_cause: str = Field(
        description="Probable underlying root cause based on symptoms and service context."
    )
    recommended_checks: list[str] = Field(
        description="List of actionable diagnostic checks and investigation steps."
    )
    suggested_resolution: str = Field(
        description="Pragmatic remediation or mitigation steps to resolve the incident."
    )
    knowledge_used: bool = Field(
        default=False,
        description="Indicates whether relevant knowledge base entries were retrieved and included in the analysis."
    )
