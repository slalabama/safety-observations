from fastapi import APIRouter, HTTPException, Request, Response, Depends
from sqlalchemy.orm import Session
import secrets
from datetime import datetime, timedelta
from pydantic import BaseModel

from app.database import SessionLocal
from app.models import Employee, Facility
from app.utils.geo import calculate_distance

router = APIRouter(prefix="/auth", tags=["Authentication"])

class LoginRequest(BaseModel):
    badge: str
    latitude: float
    longitude: float

class LoginResponse(BaseModel):
    success: bool
    message: str
    employee_name: str = None

sessions = {}

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_employee(request: Request, db: Session = Depends(get_db)):
    """Validate session and check GPS location."""
    token = request.cookies.get("session_token")
    if not token or token not in sessions:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    session_data = sessions[token]
    if session_data["expires"] < datetime.utcnow():
        del sessions[token]
        raise HTTPException(status_code=401, detail="Session expired")
    
    employee = db.query(Employee).filter(Employee.id == session_data["employee_id"]).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    return employee

@router.post("/login")
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Badge-only login with GPS geofencing."""
    
    employee = db.query(Employee).filter(Employee.badge == request.badge).first()
    if not employee:
        raise HTTPException(status_code=401, detail="Invalid badge number")
    
    facility = db.query(Facility).first()
    if not facility:
        raise HTTPException(status_code=500, detail="Facility not configured")
    
    distance_miles = calculate_distance(
        request.latitude, request.longitude,
        facility.latitude, facility.longitude
    )
    
    if distance_miles > facility.radius_miles:
        raise HTTPException(
            status_code=403,
            detail=f"You are {distance_miles:.2f} miles from facility. Max allowed: {facility.radius_miles} miles."
        )
    
    token = secrets.token_urlsafe(32)
    sessions[token] = {
        "employee_id": employee.id,
        "badge": employee.badge,
        "expires": datetime.utcnow() + timedelta(hours=12)
    }
    
    response = Response(
        content='{"success": true, "message": "Login successful", "employee_name": "' + employee.name + '"}',
        media_type="application/json"
    )
    response.set_cookie("session_token", token, httponly=True, max_age=43200)
    return response

@router.post("/logout")
def logout(request: Request):
    """Logout and clear session."""
    token = request.cookies.get("session_token")
    if token and token in sessions:
        del sessions[token]
    
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
        "department": employee.department
    }
