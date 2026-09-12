from datetime import datetime
from unittest.mock import Mock

import pytest
from sqlalchemy.exc import IntegrityError

from app.schemas.service import ServiceCreate, ServiceStatusUpdate, ServiceUpdate
from app.services.service_service import (
    ServiceNameAlreadyExistsError,
    create_service,
    update_service,
    update_service_status,
)


def test_list_services(client, db):
    create_service(db, ServiceCreate(name="payment-service", status="healthy"))
    create_service(db, ServiceCreate(name="order-service", status="degraded"))

    response = client.get("/services")

    assert response.status_code == 200
    assert [service["name"] for service in response.json()] == [
        "order-service",
        "payment-service",
    ]


def test_get_service(client, db):
    create_service(db, ServiceCreate(name="payment-service"))

    response = client.get("/services/payment-service")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_create_service_endpoint(client):
    response = client.post(
        "/services",
        json={"name": "payment-service", "description": "Handles payments"},
    )

    assert response.status_code == 201
    assert response.json()["name"] == "payment-service"
    assert response.json()["status"] == "healthy"


def test_create_duplicate_service_endpoint(client, db):
    create_service(db, ServiceCreate(name="payment-service"))

    response = client.post("/services", json={"name": "payment-service"})

    assert response.status_code == 409
    assert response.json()["detail"] == "Service name already exists"


def test_update_service_endpoint(client, db):
    create_service(db, ServiceCreate(name="payment-service"))

    response = client.patch(
        "/services/payment-service",
        json={"name": "payments", "description": "Handles payments"},
    )

    assert response.status_code == 200
    assert response.json()["name"] == "payments"
    assert response.json()["description"] == "Handles payments"


def test_update_service_preserves_unspecified_fields(client, db):
    create_service(
        db,
        ServiceCreate(name="payment-service", description="Handles payments"),
    )

    response = client.patch("/services/payment-service", json={"status": "degraded"})

    assert response.status_code == 200
    assert response.json()["name"] == "payment-service"
    assert response.json()["description"] == "Handles payments"
    assert response.json()["status"] == "degraded"


def test_update_service_status_endpoint(client, db):
    create_service(db, ServiceCreate(name="payment-service"))

    response = client.patch(
        "/services/payment-service/status",
        json={"status": "down"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "down"
    assert response.json()["last_checked_at"] is not None


def test_update_service_status_updates_timestamps(client, db):
    service = create_service(db, ServiceCreate(name="payment-service"))
    original_updated_at = service.updated_at

    response = client.patch(
        "/services/payment-service/status",
        json={"status": "degraded"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["last_checked_at"] is not None
    assert body["updated_at"] > original_updated_at.isoformat()


def test_update_duplicate_service_endpoint(client, db):
    create_service(db, ServiceCreate(name="payment-service"))
    create_service(db, ServiceCreate(name="order-service"))

    response = client.patch(
        "/services/payment-service",
        json={"name": "order-service"},
    )

    assert response.status_code == 409


def test_nonexistent_service_endpoints(client):
    update_response = client.patch(
        "/services/missing-service",
        json={"description": "Missing"},
    )
    status_response = client.patch(
        "/services/missing-service/status",
        json={"status": "down"},
    )

    assert update_response.status_code == 404
    assert status_response.status_code == 404
    assert update_response.json() == {"detail": "Service not found"}
    assert status_response.json() == {"detail": "Service not found"}


def test_service_validation_failure(client):
    response = client.post(
        "/services",
        json={"name": "payment-service", "status": "unknown"},
    )

    assert response.status_code == 422


def test_create_service_rejects_duplicate_name(db):
    create_service(db, ServiceCreate(name="payment-service"))

    with pytest.raises(ServiceNameAlreadyExistsError):
        create_service(db, ServiceCreate(name="payment-service"))


def test_create_service_rolls_back_on_duplicate_integrity_error():
    db = Mock()
    db.scalar.return_value = None
    db.commit.side_effect = IntegrityError("insert", {}, RuntimeError("duplicate"))

    with pytest.raises(ServiceNameAlreadyExistsError):
        create_service(db, ServiceCreate(name="payment-service"))

    db.rollback.assert_called_once_with()


def test_update_service_changes_details(db):
    service = create_service(db, ServiceCreate(name="payment-service"))

    updated = update_service(
        db,
        service,
        ServiceUpdate(name="payments", description="Handles payments"),
    )

    assert updated.name == "payments"
    assert updated.description == "Handles payments"


def test_update_service_status_sets_check_timestamp(db):
    service = create_service(db, ServiceCreate(name="payment-service"))
    original_updated_at = service.updated_at

    updated = update_service_status(db, service, ServiceStatusUpdate(status="down"))

    assert updated.status == "down"
    assert isinstance(updated.last_checked_at, datetime)
    assert updated.updated_at >= original_updated_at
