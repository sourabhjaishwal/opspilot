"""Delete specified users, services, and incidents from the database."""

from app.database import SessionLocal
from app.models import User, Service, Incident
from sqlalchemy import select

def delete_specified_data():
    db = SessionLocal()
    
    try:
        print("\n=== DELETING SPECIFIED DATA ===\n")
        
        # 1. Delete user: admin
        print("1. Deleting user: admin")
        user = db.scalar(select(User).where(User.username == "admin"))
        if user:
            db.delete(user)
            db.commit()
            print("   ✓ Deleted user: admin")
        else:
            print("   ✗ User not found: admin")
        
        # 2. Delete services and their related incidents
        print("\n2. Deleting services...")
        services_to_delete = [
            "ABC",
            "ANSVJK", 
            "Lethal Service API",
            "IJK",
            "New Service Micro",
            "No service"  # Also delete "No service"
        ]
        
        for svc_name in services_to_delete:
            svc = db.scalar(select(Service).where(Service.name == svc_name))
            if svc:
                # Delete related incidents first
                related_incidents = db.query(Incident).filter(Incident.service_id == svc.id).all()
                incident_count = len(related_incidents)
                for inc in related_incidents:
                    db.delete(inc)
                
                # Delete the service
                db.delete(svc)
                db.commit()
                print(f"   ✓ Deleted service: {svc_name} (with {incident_count} incident(s))")
            else:
                print(f"   ✗ Service not found: {svc_name}")
        
        # 3. Delete specific incidents
        print("\n3. Deleting specific incidents...")
        incidents_to_delete = ["INC00017", "INC00020"]
        
        for inc_num in incidents_to_delete:
            inc = db.scalar(select(Incident).where(Incident.incident_number == inc_num))
            if inc:
                db.delete(inc)
                db.commit()
                print(f"   ✓ Deleted incident: {inc_num}")
            else:
                print(f"   ✗ Incident not found: {inc_num}")
        
        # Show updated counts
        print("\n=== DELETION COMPLETE ===\n")
        print("Updated database counts:")
        print(f"  Users:     {db.query(User).count()}")
        print(f"  Services:  {db.query(Service).count()}")
        print(f"  Incidents: {db.query(Incident).count()}")
        
        # Show remaining data
        print("\n--- Remaining Users ---")
        users = db.query(User).all()
        for u in users:
            print(f"  • {u.username} ({u.role})")
        
        print("\n--- Remaining Services ---")
        services = db.query(Service).all()
        for s in services:
            print(f"  • {s.name} ({s.status})")
        
    finally:
        db.close()

if __name__ == "__main__":
    delete_specified_data()
