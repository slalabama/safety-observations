from app.database import SessionLocal
from app.models import Employee

def seed_admin():
    db = SessionLocal()
    
    existing = db.query(Employee).filter(Employee.badge == "00854").first()
    if existing:
        print(f"Admin already exists: {existing.name}")
        db.close()
        return
    
    admin = Employee(
        badge="00854",
        name="Charles Burks",
        department="HR"
    )
    
    db.add(admin)
    db.commit()
    db.refresh(admin)
    
    print("Admin user created!")
    print(f"Name: {admin.name}")
    print(f"Badge: {admin.badge}")
    db.close()

if __name__ == "__main__":
    seed_admin()
