"""Database seed script for OpsPilot local development and demonstrations."""

from datetime import datetime, timezone, timedelta
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import Base, SessionLocal, engine
from app.models.incident import Incident
from app.models.service import Service


SEED_SERVICES = [
    {
        "name": "User Management API",
        "description": "Handles user identity verification, OAuth2/OIDC token issuance, and authorization.",
        "status": "degraded",
        "incidents": [
            {
                "severity": "high",
                "status": "investigating",
                "title": "Intermittent HTTP 401/403 Errors on Token Validation",
                "description": "Auth proxy intermittently returning 401 Unauthorized for valid JWT bearer tokens due to edge clock skew.",
                "hours_ago": 3,
            },
            {
                "severity": "medium",
                "status": "resolved",
                "title": "LDAP Directory Sync Connection Timeout",
                "description": "Nightly user directory synchronization job timed out after 300s due to socket disconnect on identity provider endpoint.",
                "hours_ago": 28,
            },
        ],
    },
    {
        "name": "Payment API",
        "description": "Processes credit card transactions, digital wallet payments, and provider webhooks.",
        "status": "down",
        "incidents": [
            {
                "severity": "critical",
                "status": "open",
                "title": "Payment Processing Latency Spike and Webhook Backlog",
                "description": "Payment latency surged to 9,200ms; inbound payment gateway webhook backlog exceeded 4,500 events.",
                "hours_ago": 1,
            },
            {
                "severity": "high",
                "status": "resolved",
                "title": "HTTP 500 Errors on Card Settlement Endpoint",
                "description": "Card settlement batch endpoint threw 500 Internal Server Error following an unhandled precision error in currency conversion.",
                "hours_ago": 48,
            },
        ],
    },
    {
        "name": "Order Management API",
        "description": "Manages order lifecycles, inventory reservations, and checkout pipelines.",
        "status": "degraded",
        "incidents": [
            {
                "severity": "high",
                "status": "investigating",
                "title": "Orders Stuck in Pending Processing State",
                "description": "Checkout completion events failing to transition order status from pending to confirmed due to lock contention.",
                "hours_ago": 4,
            },
            {
                "severity": "critical",
                "status": "open",
                "title": "Failed Database Connections in Checkout Thread Pool",
                "description": "Order checkout workers threw pool timeout exceptions (QueuePool limit reached) during traffic surge.",
                "hours_ago": 2,
            },
        ],
    },
    {
        "name": "Notification Service",
        "description": "Dispatches transactional emails, SMS notifications, and push alerts.",
        "status": "healthy",
        "incidents": [
            {
                "severity": "medium",
                "status": "open",
                "title": "Delayed Transactional Email Dispatch",
                "description": "Outbound order confirmation emails experiencing a 25-minute queue lag caused by rate-limit throttling on SMTP gateway.",
                "hours_ago": 6,
            },
            {
                "severity": "low",
                "status": "resolved",
                "title": "SMS Gateway 502 Bad Gateway Response Spike",
                "description": "SMS provider returned sporadic HTTP 502 responses during maintenance window; retries drained queue.",
                "hours_ago": 72,
            },
        ],
    },
    {
        "name": "Reporting Service",
        "description": "Generates asynchronous business intelligence reports and data exports.",
        "status": "degraded",
        "incidents": [
            {
                "severity": "high",
                "status": "open",
                "title": "Nightly Reconciliation Report Generation Failure",
                "description": "Scheduled nightly reconciliation worker terminated unexpectedly with OOM error during full-table scan.",
                "hours_ago": 8,
            },
            {
                "severity": "medium",
                "status": "investigating",
                "title": "Increased API Latency on Analytics Export Endpoint",
                "description": "CSV export endpoint latency degraded from 1.5s to 42s due to missing composite index on query predicates.",
                "hours_ago": 12,
            },
        ],
    },
]

def seed_database(db: Session | None = None) -> dict[str, int]:
    """Populate SQLite database with fictional services and incidents idempotently."""
    Base.metadata.create_all(bind=engine)
    should_close = False
    if db is None:
        db = SessionLocal()
        should_close = True

    services_created = 0
    services_existing = 0
    incidents_created = 0
    incidents_existing = 0

    try:
        now = datetime.now(timezone.utc)
        for svc_data in SEED_SERVICES:
            service = db.scalar(select(Service).where(Service.name == svc_data["name"]))
            if service is None:
                service = Service(
                    name=svc_data["name"],
                    description=svc_data["description"],
                    status=svc_data["status"],
                    last_checked_at=now,
                    created_at=now - timedelta(days=7),
                    updated_at=now,
                )
                db.add(service)
                db.commit()
                db.refresh(service)
                services_created += 1
                print(f"  [+] Created Service: {service.name} (ID: {service.id})")
            else:
                services_existing += 1
                print(f"  [.] Existing Service: {service.name} (ID: {service.id})")

            for inc_data in svc_data["incidents"]:
                incident = db.scalar(
                    select(Incident).where(
                        Incident.service_id == service.id,
                        Incident.title == inc_data["title"],
                    )
                )
                if incident is None:
                    created_time = now - timedelta(hours=inc_data["hours_ago"])
                    incident = Incident(
                        service_id=service.id,
                        severity=inc_data["severity"],
                        status=inc_data["status"],
                        title=inc_data["title"],
                        description=inc_data["description"],
                        created_at=created_time,
                        updated_at=created_time if inc_data["status"] != "resolved" else now,
                    )
                    db.add(incident)
                    db.commit()
                    incidents_created += 1
                    print(f"      [+] Created Incident: [{inc_data['severity'].upper()}] {inc_data['title']}")
                else:
                    incidents_existing += 1
                    print(f"      [.] Existing Incident: [{incident.severity.upper()}] {incident.title}")

        return {
            "services_created": services_created,
            "services_existing": services_existing,
            "incidents_created": incidents_created,
            "incidents_existing": incidents_existing,
        }
    finally:
        if should_close:
            db.close()


if __name__ == "__main__":
    print("\n==========================================")
    print(" OpsPilot Database Seeder")
    print("==========================================")
    result = seed_database()
    print("\n--- Summary ---")
    print(f"Services:  {result['services_created']} created, {result['services_existing']} already existed")
    print(f"Incidents: {result['incidents_created']} created, {result['incidents_existing']} already existed")
    print("Database seeding completed successfully.\n")

