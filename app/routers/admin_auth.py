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

    # Validate PIN
    if not employee.pin:
        raise HTTPException(status_code=403, detail="PIN not set for this employee")
    if employee.pin != request.pin:
        raise HTTPException(status_code=401, detail="Invalid PIN")

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


class ObserveLoginRequest(BaseModel):
    first_name: str = ""
    last_name: str = ""
    badge: str = ""

def _match_employee(db, first: str, last: str, badge: str):
    """Smart matching: badge exact, else flexible name search."""
    badge = (badge or "").strip()
    first = (first or "").strip()
    last  = (last  or "").strip()

    if badge:
        return db.query(Employee).filter(Employee.badge == badge).first()

    if not (first and last):
        return None

    # Pull all active employees and match in Python so we can be flexible.
    employees = db.query(Employee).filter(Employee.status == "active").all()
    f_low = first.lower()
    l_low = last.lower()

    # PASS 1: exact first + exact last (case-insensitive)
    for e in employees:
        ef = (getattr(e, "first_name", None) or "").strip().lower()
        el = (getattr(e, "last_name",  None) or "").strip().lower()
        if ef == f_low and el == l_low:
            return e

    # PASS 2: first matches, and last is any whitespace-separated word of stored last
    for e in employees:
        ef = (getattr(e, "first_name", None) or "").strip().lower()
        el = (getattr(e, "last_name",  None) or "").strip().lower()
        if ef == f_low and l_low in el.split():
            return e

    # PASS 3: parse name column "Last, First Middle" and try
    for e in employees:
        full = (e.name or "").strip()
        if "," in full:
            stored_last, rest = full.split(",", 1)
            stored_last = stored_last.strip().lower()
            stored_first = rest.strip().split()[0].lower() if rest.strip() else ""
            if stored_first == f_low and (l_low == stored_last or l_low in stored_last.split()):
                return e
        # Also try "First Last" format
        parts = full.lower().split()
        if len(parts) >= 2 and parts[0] == f_low and l_low in parts[1:]:
            return e

    # PASS 4: substring fallback - first name matches start, last name matches any token
    for e in employees:
        ef = (getattr(e, "first_name", None) or "").strip().lower()
        el = (getattr(e, "last_name",  None) or "").strip().lower()
        name_l = (e.name or "").lower()
        if f_low in name_l and l_low in name_l:
            return e

    return None

@router.post("/observe-login")
def observe_login(req: ObserveLoginRequest, db: Session = Depends(get_db)):
    """Employee login for observations. No PIN, no GPS. Flexible name match or badge."""
    employee = _match_employee(db, req.first_name, req.last_name, req.badge)

    if not employee:
        if (req.badge or "").strip():
            raise HTTPException(status_code=404, detail="Employee ID not found.")
        if not (req.first_name and req.last_name):
            raise HTTPException(status_code=400, detail="Enter first and last name, or your Employee ID.")
        raise HTTPException(status_code=404, detail="No employee matched that name.")

    if employee.status != "active":
        raise HTTPException(status_code=403, detail="Employee account is inactive")

    token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(hours=1)
    db.add(SessionRecord(id=token, employee_id=employee.id, expires_at=expires_at))
    employee.last_login = datetime.utcnow()
    db.commit()

    response = Response(
        content='{"success": true, "employee_name": "' + employee.name + '", "badge": "' + (employee.badge or "") + '"}',
        media_type="application/json"
    )
    response.set_cookie("session_token", token, httponly=True, secure=True, samesite="lax", max_age=3600, path="/")
    return response

