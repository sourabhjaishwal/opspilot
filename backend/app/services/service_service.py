import asyncio
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.exceptions import ServiceNameAlreadyExistsError
from app.models.service import Service
from app.schemas.service import ServiceCreate, ServiceStatusUpdate, ServiceUpdate

logger = logging.getLogger(__name__)


def create_service(db: Session, service_data: ServiceCreate) -> Service:
    existing_service = db.scalar(select(Service).where(Service.name == service_data.name))
    if existing_service is not None:
        raise ServiceNameAlreadyExistsError(service_data.name)

    service = Service(**service_data.model_dump())
    db.add(service)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ServiceNameAlreadyExistsError(service_data.name) from exc
    db.refresh(service)
    return service


def list_services(db: Session) -> list[Service]:
    statement = select(Service).order_by(Service.name)
    return list(db.scalars(statement).all())


def get_service(db: Session, service_name: str) -> Service | None:
    return db.scalar(select(Service).where(Service.name == service_name))


def update_service(db: Session, service: Service, service_data: ServiceUpdate) -> Service:
    update_data = service_data.model_dump(exclude_unset=True)
    new_name = update_data.get("name")
    if new_name is not None and new_name != service.name:
        existing_service = db.scalar(select(Service).where(Service.name == new_name))
        if existing_service is not None:
            raise ServiceNameAlreadyExistsError(new_name)

    status = update_data.pop("status", None)
    for field, value in update_data.items():
        setattr(service, field, value)
    if status is not None:
        _set_service_status(service, status)
    service.updated_at = datetime.now(timezone.utc)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ServiceNameAlreadyExistsError(new_name or service.name) from exc
    db.refresh(service)
    return service


def update_service_status(
    db: Session,
    service: Service,
    status_data: ServiceStatusUpdate,
) -> Service:
    _set_service_status(service, status_data.status)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise
    db.refresh(service)
    return service


def _set_service_status(service: Service, status: str) -> None:
    now = datetime.now(timezone.utc)
    service.status = status
    service.last_checked_at = now
    service.updated_at = now


async def poll_services_for_health() -> None:
    while True:
        try:
            db = SessionLocal()
            now = datetime.now(timezone.utc)
            services = db.scalars(select(Service)).all()
            for service in services:
                if service.status == "down":
                    continue
                if service.last_checked_at is None or now - service.last_checked_at > timedelta(minutes=5):
                    service.status = "degraded"
                    service.last_checked_at = now
                    service.updated_at = now
                    logger.warning("Health poll marked service degraded: %s", service.name)
                else:
                    service.status = "healthy"
                    service.last_checked_at = now
                    service.updated_at = now
            db.commit()
            db.close()
        except Exception as exc:  # pragma: no cover - defensive background monitoring
            logger.exception("Health poll failed: %s", exc)
        await asyncio.sleep(60)


def start_service_health_monitor() -> asyncio.Task[None]:
    return asyncio.create_task(poll_services_for_health())
