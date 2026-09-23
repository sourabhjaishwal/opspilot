import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.incident import Incident
from app.models.service import Service
from app.scripts.seed import SEED_SERVICES, seed_database


def test_seed_database_creates_records(db: Session):
    '''Verify that running seed_database creates the expected services and incidents.'''
    result = seed_database(db=db)

    assert result["services_created"] == len(SEED_SERVICES)
    assert result["services_created"] >= 5
    assert result["incidents_created"] >= 10

    # Verify services exist in DB
    services = db.scalars(select(Service)).all()
    assert len(services) == len(SEED_SERVICES)
    service_names = {s.name for s in services}
    assert "User Management API" in service_names
    assert "Payment API" in service_names
    assert "Order Management API" in service_names
    assert "Notification Service" in service_names
    assert "Reporting Service" in service_names

    # Verify incidents exist and are properly linked
    incidents = db.scalars(select(Incident)).all()
    assert len(incidents) >= 10
    for inc in incidents:
        assert inc.service_id is not None
        assert inc.service is not None
        assert inc.severity in {"low", "medium", "high", "critical"}
        assert inc.status in {"open", "investigating", "resolved"}


def test_seed_database_is_idempotent(db: Session):
    '''Running seed_database a second time should not create duplicate entries.'''
    first_run = seed_database(db=db)
    assert first_run["services_created"] > 0
    assert first_run["incidents_created"] > 0

    second_run = seed_database(db=db)
    assert second_run["services_created"] == 0
    assert second_run["incidents_created"] == 0
    assert second_run["services_existing"] == first_run["services_created"]
    assert second_run["incidents_existing"] == first_run["incidents_created"]

