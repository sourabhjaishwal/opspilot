from datetime import datetime

import pytest

from app.models.incident import Incident
from app.schemas.service import ServiceCreate
from app.services.service_service import create_service


INCIDENT = {
    "service": "payment-service",
    "severity": "high",
    "title": "Health endpoint returning 503",
    "description": "The payment service health endpoint is returning HTTP 503.",
}


@pytest.fixture()
def registered_service(db):
    create_service(db, ServiceCreate(name="payment-service"))


@pytest.fixture()
def registered_services(db):
    create_service(db, ServiceCreate(name="payment-service"))
    create_service(db, ServiceCreate(name="order-service"))
    create_service(db, ServiceCreate(name="notification-service"))


def create_incident(client, service="payment-service", severity="high", title="Incident"):
    response = client.post(
        "/incidents",
        json={
            "service": service,
            "severity": severity,
            "title": title,
            "description": "Test incident description",
        },
    )
    assert response.status_code == 201
    return response.json()


def test_create_incident(client, registered_service):
    response = client.post("/incidents", json=INCIDENT)

    assert response.status_code == 201
    body = response.json()
    assert body["service"] == INCIDENT["service"]
    assert body["severity"] == "high"
    assert body["status"] == "open"
    assert body["id"] == 1


def test_list_incidents(client, registered_service):
    client.post("/incidents", json=INCIDENT)

    response = client.get("/incidents")

    assert response.status_code == 200
    assert len(response.json()["items"]) == 1
    assert response.json()["page"] == 1
    assert response.json()["page_size"] == 20
    assert response.json()["total"] == 1


def test_get_incident(client, registered_service):
    created = client.post("/incidents", json=INCIDENT).json()

    response = client.get(f"/incidents/{created['id']}")

    assert response.status_code == 200
    assert response.json()["title"] == INCIDENT["title"]


def test_get_nonexistent_incident(client):
    response = client.get("/incidents/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Incident not found"


def test_update_incident_status(client, registered_service):
    created = client.post("/incidents", json=INCIDENT).json()

    response = client.patch(
        f"/incidents/{created['id']}",
        json={"status": "investigating"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "investigating"


def test_create_incident_with_unknown_service_returns_not_found(client):
    response = client.post("/incidents", json=INCIDENT)

    assert response.status_code == 404
    assert response.json() == {"detail": "Service not found"}


def test_default_pagination_and_total(client, registered_service):
    for index in range(25):
        create_incident(client, title=f"Incident {index}")

    response = client.get("/incidents")

    assert response.status_code == 200
    assert len(response.json()["items"]) == 20
    assert response.json()["page"] == 1
    assert response.json()["page_size"] == 20
    assert response.json()["total"] == 25


def test_filter_by_service(client, registered_services):
    create_incident(client, service="payment-service")
    create_incident(client, service="order-service")

    response = client.get("/incidents?service=order-service")

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["service"] == "order-service"


def test_filter_by_severity(client, registered_service):
    create_incident(client, severity="high")
    create_incident(client, severity="low")

    response = client.get("/incidents?severity=low")

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["severity"] == "low"


def test_filter_by_status(client, registered_service):
    created = create_incident(client)
    create_incident(client)
    client.patch(f"/incidents/{created['id']}", json={"status": "investigating"})

    response = client.get("/incidents?status=investigating")

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["status"] == "investigating"


def test_combined_filters_use_and_logic(client, registered_services):
    matching = create_incident(
        client,
        service="order-service",
        severity="critical",
        title="Matching incident",
    )
    client.patch(f"/incidents/{matching['id']}", json={"status": "resolved"})
    create_incident(client, service="order-service", severity="critical")
    create_incident(client, service="payment-service", severity="critical")

    response = client.get(
        "/incidents?service=order-service&severity=critical&status=resolved"
    )

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["title"] == "Matching incident"


def test_page_and_page_size(client, registered_service):
    created = [create_incident(client, title=f"Incident {index}") for index in range(5)]

    response = client.get("/incidents?page=2&page_size=2")

    assert response.status_code == 200
    assert response.json()["page"] == 2
    assert response.json()["page_size"] == 2
    assert response.json()["total"] == 5
    assert [item["id"] for item in response.json()["items"]] == [
        created[2]["id"],
        created[1]["id"],
    ]


def test_pagination_boundary_returns_single_item(client, registered_service):
    created = [create_incident(client, title=f"Incident {index}") for index in range(2)]

    response = client.get("/incidents?page=1&page_size=1")

    assert response.status_code == 200
    assert response.json()["page"] == 1
    assert response.json()["page_size"] == 1
    assert response.json()["total"] == 2
    assert [item["id"] for item in response.json()["items"]] == [created[1]["id"]]


def test_empty_page_preserves_matching_total(client, registered_service):
    create_incident(client, title="Incident 1")
    create_incident(client, title="Incident 2")

    response = client.get("/incidents?page=3&page_size=1")

    assert response.status_code == 200
    assert response.json()["items"] == []
    assert response.json()["page"] == 3
    assert response.json()["page_size"] == 1
    assert response.json()["total"] == 2


def test_deterministic_ordering_uses_id_as_tiebreaker(client, db, registered_service):
    created_at = datetime(2026, 1, 1)
    service = db.query(type("ServiceQuery", (), {"__getattr__": lambda self, name: None})()).all() if False else db.execute(
        __import__("sqlalchemy").sql.select(__import__("app.models.service", fromlist=["Service"]).Service)
    ).scalar_one()
    incidents = [
        Incident(
            service_id=service.id,
            severity="high",
            status="open",
            title=f"Incident {index}",
            description="Test incident description",
            created_at=created_at,
            updated_at=created_at,
        )
        for index in range(3)
    ]
    db.add_all(incidents)
    db.commit()

    response = client.get("/incidents")

    assert [item["id"] for item in response.json()["items"]] == [3, 2, 1]


@pytest.mark.parametrize("query", ["page=0", "page_size=0", "page_size=101"])
def test_invalid_pagination_parameters_return_validation_error(client, query):
    response = client.get(f"/incidents?{query}")

    assert response.status_code == 422
