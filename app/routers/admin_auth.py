from fastapi import APIRouter, HTTPException, Request, Response, Depends
from sqlalchemy.orm import Session
import secrets
from datetime import datetime, timedelta
from pydantic import BaseModel

from app.database import SessionLocal
from app.models import Employee, Facility, SessionRecord
from app.utils.geo import calculate_distance

router = APIRouter(prefix="/auth", tags=["Authentication"])

class LoginRequest(BaseModel):
    first_name: str
    last_name: str
    pin: str

class LoginResponse(BaseModel):
    success: bool
    message: str
    employee_name: str = None

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_employee(request: Request, db: Session = Depends(get_db)):
    """Validate session and check GPS location."""
    token = request.cookies.get("session_token")
    if not token:
        raise HTTPException(status_code=401, detail="Unauthorized")

    session_record = db.query(SessionRecord).filter(SessionRecord.id == token).first()
    if not session_record:
        raise HTTPException(status_code=401, detail="Unauthorized")

    if session_record.expires_at < datetime.utcnow():
        db.delete(session_record)
        db.commit()
        raise HTTPException(status_code=401, detail="Session expired")

    # Extend session on each request
    session_record.expires_at = datetime.utcnow() + timedelta(hours=1)
    db.commit()

    employee = session_record.employee
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    if employee.status != "active":
        raise HTTPException(status_code=403, detail="Employee account is inactive")

    return employee

@router.post("/login")
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """First/Last name login with GPS geofencing."""

    full_name = (request.first_name.strip() + " " + request.last_name.strip()).strip()
    employee = db.query(Employee).filter(Employee.name.ilike(full_name)).first()
    if not employee:
        raise HTTPException(status_code=401, detail="Name not found in system")

    if employee.status != "active":
        raise HTTPException(status_code=403, detail="Employee account is inactive")

    facility = db.query(Facility).first()
    if not facility:
        raise HTTPException(status_code=500, detail="Facility not configured")

    # Admins bypass GPS fence
    if employee.role != 'admin':
        distance_miles = calculate_distance(
            request.latitude, request.longitude,
            facility.latitude, facility.longitude
        )

        if distance_miles > facility.radius_miles:
            raise HTTPException(
                status_code=403,
                detail=f"You are {distance_miles:.2f} miles from facility. Max allowed: {facility.radius_miles} miles."
            )

    # Create DB session (7-day timeout)
    token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(days=7)

    session_record = SessionRecord(
        id=token,
        employee_id=employee.id,
        expires_at=expires_at
    )
    db.add(session_record)

    # Update last_login
    employee.last_login = datetime.utcnow()
    db.commit()

    response = Response(
        content='{"success": true, "message": "Login successful", "employee_name": "' + employee.name + '"}',
        media_type="application/json"
    )
    response.set_cookie("session_token", token, httponly=True, secure=True, samesite="lax", max_age=604800, path="/")
    return response

@router.post("/logout")
def logout(request: Request, db: Session = Depends(get_db)):
    """Logout and clear session."""
    token = request.cookies.get("session_token")
    if token:
        session_record = db.query(SessionRecord).filter(SessionRecord.id == token).first()
        if session_record:
            db.delete(session_record)
            db.commit()

    response = Response(content='{"success": true, "message": "Logged out"}', media_type="application/json")
    response.delete_cookie("session_token")
    return response

@router.get("/me")
def get_current_user(employee: Employee = Depends(get_current_employee)):
    """Get current logged-in employee."""
    return {
        "id": employee.id,
        "badge": employee.badge,
        "name": employee.name,
        "department": employee.department,
        "role": employee.role,
        "status": employee.status
    }

