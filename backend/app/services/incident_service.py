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
    IncidentResponse,
    IncidentStatus,
    IncidentUpdate,
    Severity,
)

logger = logging.getLogger(__name__)


def _serialize_incident(incident: Incident) -> IncidentResponse:
    return IncidentResponse(
        id=incident.id,
        service_id=incident.service_id,
        service=incident.service.name if incident.service is not None else "",
        severity=incident.severity,
        status=incident.status,
        title=incident.title,
        description=incident.description,
        created_at=incident.created_at,
        updated_at=incident.updated_at,
    )


def create_incident(db: Session, incident_data: IncidentCreate) -> IncidentResponse:
    service_name = incident_data.service
    service_id = incident_data.service_id

    if service_id is not None:
        service = db.get(Service, service_id)
        if service is None:
            raise ServiceNotFoundError(f"service_id={service_id}")
    else:
        service = db.scalar(select(Service).where(Service.name == service_name))
        if service is None:
            raise ServiceNotFoundError(service_name or "")

    payload = incident_data.model_dump(exclude={"service", "service_id"})
    incident = Incident(service_id=service.id, **payload)
    db.add(incident)
    db.commit()
    db.refresh(incident)
    logger.info("Incident created: id=%s service=%s", incident.id, service.name)
    return _serialize_incident(incident)


def list_incidents(
    db: Session,
    service: str | None = None,
    severity: Severity | None = None,
    status: IncidentStatus | None = None,
    page: int = 1,
    page_size: int = 20,
) -> IncidentListResponse:
    statement = select(Incident).join(Service, Incident.service_id == Service.id)
    filters = []
    if service is not None:
        filters.append(Service.name == service)
    if severity is not None:
        filters.append(Incident.severity == severity)
    if status is not None:
        filters.append(Incident.status == status)

    if filters:
        statement = statement.where(*filters)

    total = db.scalar(select(func.count()).select_from(statement.subquery())) or 0
    incidents = list(
        db.scalars(
            statement
            .order_by(Incident.created_at.desc(), Incident.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()
    )
    return IncidentListResponse(
        items=[_serialize_incident(incident) for incident in incidents],
        page=page,
        page_size=page_size,
        total=total,
    )


def get_incident(db: Session, incident_id: int) -> Incident | None:
    return db.get(Incident, incident_id)


def update_incident(db: Session, incident: Incident, incident_data: IncidentUpdate) -> IncidentResponse:
    incident.status = incident_data.status
    incident.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(incident)
    logger.info("Incident updated: id=%s status=%s", incident.id, incident.status)
    return _serialize_incident(incident)
