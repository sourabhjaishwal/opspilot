import logging
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.exceptions import ServiceNotFoundError
from app.models.incident import Incident
from app.models.service import Service
from app.schemas.incident import (
    IncidentCreate,
    IncidentListResponse,
    IncidentStatus,
    IncidentUpdate,
    Severity,
)

logger = logging.getLogger(__name__)


def create_incident(db: Session, incident_data: IncidentCreate) -> Incident:
    service = db.scalar(select(Service).where(Service.name == incident_data.service))
    if service is None:
        raise ServiceNotFoundError(incident_data.service)

    incident = Incident(**incident_data.model_dump())
    db.add(incident)
    db.commit()
    db.refresh(incident)
    logger.info("Incident created: id=%s service=%s", incident.id, incident.service)
    return incident


def list_incidents(
    db: Session,
    service: str | None = None,
    severity: Severity | None = None,
    status: IncidentStatus | None = None,
    page: int = 1,
    page_size: int = 20,
) -> IncidentListResponse:
    filters = []
    if service is not None:
        filters.append(Incident.service == service)
    if severity is not None:
        filters.append(Incident.severity == severity)
    if status is not None:
        filters.append(Incident.status == status)

    matching_incidents = select(Incident).where(*filters)
    total = db.scalar(select(func.count()).select_from(matching_incidents.subquery())) or 0
    incidents = list(
        db.scalars(
            matching_incidents
            .order_by(Incident.created_at.desc(), Incident.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()
    )
    return IncidentListResponse(
        items=incidents,
        page=page,
        page_size=page_size,
        total=total,
    )


def get_incident(db: Session, incident_id: int) -> Incident | None:
    return db.get(Incident, incident_id)


def update_incident(db: Session, incident: Incident, incident_data: IncidentUpdate) -> Incident:
    incident.status = incident_data.status
    incident.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(incident)
    logger.info("Incident updated: id=%s status=%s", incident.id, incident.status)
    return incident
