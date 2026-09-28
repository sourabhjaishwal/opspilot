from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.exceptions import IncidentNotFoundError
from app.schemas.ai import AIIncidentAnalysis
from app.schemas.incident import (
    IncidentCreate,
    IncidentListResponse,
    IncidentResponse,
    IncidentStatus,
    IncidentUpdate,
    Severity,
)
from app.services import ai_service, incident_service
from app.routes.deps import get_current_user

router = APIRouter(prefix="/incidents", tags=["incidents"])


@router.post("", response_model=IncidentResponse, status_code=status.HTTP_201_CREATED)
def create_incident(
    incident_data: IncidentCreate,
    db: Session = Depends(get_db),
    _: object = Depends(get_current_user),
) -> IncidentResponse:
    return incident_service.create_incident(db, incident_data)


@router.get("", response_model=IncidentListResponse)
def list_incidents(
    service: str | None = None,
    severity: Severity | None = None,
    status: IncidentStatus | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: object = Depends(get_current_user),
) -> IncidentListResponse:
    return incident_service.list_incidents(db, service, severity, status, page, page_size)


@router.get("/{incident_id}", response_model=IncidentResponse)
def get_incident(
    incident_id: int,
    db: Session = Depends(get_db),
    _: object = Depends(get_current_user),
) -> IncidentResponse:
    incident = incident_service.get_incident(db, incident_id)
    if incident is None:
        raise IncidentNotFoundError(incident_id)
    return incident_service._serialize_incident(incident)


@router.patch("/{incident_id}", response_model=IncidentResponse)
def update_incident(
    incident_id: int,
    incident_data: IncidentUpdate,
    db: Session = Depends(get_db),
    _: object = Depends(get_current_user),
) -> IncidentResponse:
    incident = incident_service.get_incident(db, incident_id)
    if incident is None:
        raise IncidentNotFoundError(incident_id)
    return incident_service.update_incident(db, incident, incident_data)


@router.post("/{incident_id}/analyze", response_model=AIIncidentAnalysis)
def analyze_incident(
    incident_id: int,
    db: Session = Depends(get_db),
    _: object = Depends(get_current_user),
) -> AIIncidentAnalysis:
    incident = incident_service.get_incident(db, incident_id)
    if incident is None:
        raise IncidentNotFoundError(incident_id)
    try:
        return ai_service.analyze_incident(incident)
    except ValueError as exc:
        # Rate limit error from ai_service
        from fastapi import HTTPException
        raise HTTPException(status_code=429, detail=str(exc)) from exc
