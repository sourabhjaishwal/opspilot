from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.exceptions import ServiceNotFoundError
from app.schemas.service import (
    ServiceCreate,
    ServiceResponse,
    ServiceStatusUpdate,
    ServiceUpdate,
)
from app.services import service_service

router = APIRouter(prefix="/services", tags=["services"])


@router.post("", response_model=ServiceResponse, status_code=status.HTTP_201_CREATED)
def create_service(service_data: ServiceCreate, db: Session = Depends(get_db)) -> ServiceResponse:
    return service_service.create_service(db, service_data)


@router.get("", response_model=list[ServiceResponse])
def list_services(db: Session = Depends(get_db)) -> list[ServiceResponse]:
    return service_service.list_services(db)


@router.get("/{service_name}")
def get_service(service_name: str, db: Session = Depends(get_db)) -> ServiceResponse:
    service = service_service.get_service(db, service_name)
    if service is None:
        raise ServiceNotFoundError(service_name)
    return service


@router.patch("/{service_name}", response_model=ServiceResponse)
def update_service(
    service_name: str,
    service_data: ServiceUpdate,
    db: Session = Depends(get_db),
) -> ServiceResponse:
    service = service_service.get_service(db, service_name)
    if service is None:
        raise ServiceNotFoundError(service_name)
    return service_service.update_service(db, service, service_data)


@router.patch("/{service_name}/status", response_model=ServiceResponse)
def update_service_status(
    service_name: str,
    status_data: ServiceStatusUpdate,
    db: Session = Depends(get_db),
) -> ServiceResponse:
    service = service_service.get_service(db, service_name)
    if service is None:
        raise ServiceNotFoundError(service_name)
    return service_service.update_service_status(db, service, status_data)
