"""Database seed script for OpsPilot local development and demonstrations."""

from datetime import datetime, timezone, timedelta
from sqlalchemy import func, select
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
                "description": "Transactional email delivery delayed by 15-30 minutes for order confirmations and password reset flows.",
                "hours_ago": 6,
            },
            {
                "severity": "low",
                "status": "resolved",
                "title": "Push Notification Token Expiry Spike",
                "description": "Mobile push notification delivery rate dropped 12% due to batch of expired device tokens not pruned from registry.",
                "hours_ago": 36,
            },
        ],
    },
    {
        "name": "Inventory Service",
        "description": "Tracks product stock levels, manages reservations, and coordinates warehouse sync.",
        "status": "healthy",
        "incidents": [
            {
                "severity": "low",
                "status": "resolved",
                "title": "Inventory Cache Inconsistency After Deployment",
                "description": "Product stock counts briefly incorrect after deployment flushed in-memory cache without warming.",
                "hours_ago": 12,
            },
            {
                "severity": "high",
                "status": "open",
                "title": "Warehouse Sync Service Connection Failure",
                "description": "Real-time warehouse inventory sync failing due to ERP database connection pool exhaustion.",
                "hours_ago": 5,
            },
        ],
    },
    {
        "name": "Reporting Service",
        "description": "Generates real-time and scheduled operational analytics, dashboards, and export reports.",
        "status": "degraded",
        "incidents": [
            {
                "severity": "medium",
                "status": "investigating",
                "title": "Dashboard Query Timeout on Large Date Ranges",
                "description": "Reporting dashboard queries timing out for date ranges exceeding 90 days due to missing composite index.",
                "hours_ago": 8,
            },
            {
                "severity": "low",
                "status": "resolved",
                "title": "Scheduled Report Export Email Delivery Failure",
                "description": "Nightly CSV report exports failed to send via email due to SMTP credential rotation without config update.",
                "hours_ago": 20,
            },
        ],
    },
]


def _next_incident_number(db: Session) -> str:
    """Generate the next incident number based on current max numeric incident_number or id."""
    incidents = db.scalars(select(Incident)).all()
    max_num = 0
    for inc in incidents:
        if inc.incident_number and inc.incident_number.startswith("INC"):
            try:
                num = int(inc.incident_number[3:])
                if num > max_num:
                    max_num = num
            except ValueError:
                pass
        if inc.id and inc.id > max_num:
            max_num = inc.id
    next_number = max_num + 1
    return f"INC{next_number:05d}"


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
                    inc_number = _next_incident_number(db)
                    incident = Incident(
                        incident_number=inc_number,
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
                    print(f"      [+] Created Incident: {inc_number} [{inc_data['severity'].upper()}] {inc_data['title']}")
                else:
                    if incident.incident_number is None:
                        incident.incident_number = _next_incident_number(db)
                        db.commit()
                        print(f"      [~] Backfilled number {incident.incident_number} for: {incident.title}")
                    incidents_existing += 1
                    print(f"      [.] Existing Incident: {incident.incident_number} [{incident.severity.upper()}] {incident.title}")

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
