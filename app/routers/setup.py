from fastapi import APIRouter
from app.database import SessionLocal, Base, engine
from app.models import Employee, Facility

router = APIRouter()

@router.get("/setup")
def setup():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    if not db.query(Facility).first():
        db.add(Facility(name="Main Facility", latitude=32.9321, longitude=-85.9618, radius_miles=2.0))
    
    if not db.query(Employee).filter(Employee.badge == "00854").first():
        db.add(Employee(badge="00854", name="Charles Burks", department="HR", role="admin"))
    
    db.commit()
    db.close()
    return {"status": "Setup complete! You can now login with badge 00854"}
