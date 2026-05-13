from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Request
from sqlalchemy.orm import Session
import csv
import io
from pydantic import BaseModel
from typing import Optional

from app.database import SessionLocal
from app.models import Employee
from app.routers.admin_auth import get_current_employee

router = APIRouter(prefix="/users", tags=["Users"])

class EmployeeCreate(BaseModel):
    name: str
    department: Optional[str] = None
    role: str = "basic"
    email: Optional[str] = None
    pin: Optional[str] = None

class EmployeeResponse(BaseModel):
    id: int
    name: str
    department: Optional[str] = None
    role: str = "basic"
    email: Optional[str] = None
    pin: Optional[str] = None

class CSVImportResponse(BaseModel):
    total: int
    imported: int
    skipped: int
    duplicates: list

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/import-csv")
async def import_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    admin: Employee = Depends(get_current_employee)
):
    """
    Import employees from CSV.
    Accepted headers (case-insensitive): badge, name, first_name, last_name, department, role, email
    Matches by badge (unique); skips dupes.
    """
    contents = await file.read()
    text = contents.decode("utf-8-sig")
    sample = text[:500]
    delim = "	" if "	" in sample else ","
    reader = csv.DictReader(io.StringIO(text), delimiter=delim)
    # Normalize header names
    reader.fieldnames = [(h or "").strip().lower().replace(" ", "_") for h in (reader.fieldnames or [])]

    imported = 0
    skipped = 0
    duplicates = []
    total = 0
    for idx, row in enumerate(reader, 1):
        total += 1
        try:
            badge = (row.get("badge") or row.get("emp_id") or row.get("employee_id") or "").strip()
            name  = (row.get("name") or "").strip()
            first = (row.get("first_name") or row.get("first") or "").strip()
            last  = (row.get("last_name")  or row.get("last")  or "").strip()
            dept  = (row.get("department") or row.get("position") or "").strip() or None
            role  = (row.get("role") or "basic").strip().lower() or "basic"
            email = (row.get("email") or "").strip() or None

            if not name and first and last:
                name = f"{first} {last}".strip()
            if not name:
                skipped += 1
                duplicates.append({"row": idx, "error": "no name"})
                continue
            if not badge:
                skipped += 1
                duplicates.append({"row": idx, "name": name, "error": "no badge/emp id"})
                continue

            existing = db.query(Employee).filter(Employee.badge == badge).first()
            if existing:
                # Update first/last/position if we now have them
                if first and not existing.first_name: existing.first_name = first
                if last  and not existing.last_name:  existing.last_name  = last
                if dept and not existing.department:  existing.department = dept
                duplicates.append({"row": idx, "name": name, "badge": badge})
                skipped += 1
                continue

            db.add(Employee(
                badge=badge,
                name=name,
                first_name=first or None,
                last_name=last or None,
                department=dept,
                role=role,
                email=email,
                status="active",
            ))
            try:
                db.flush()
                imported += 1
            except Exception as e:
                db.rollback()
                skipped += 1
                duplicates.append({"row": idx, "name": name, "error": str(e)})
        except Exception as e:
            skipped += 1
            duplicates.append({"row": idx, "error": str(e)})

    db.commit()
    return CSVImportResponse(total=total, imported=imported, skipped=skipped, duplicates=duplicates)


@router.post("/add")
def add_employee(
    emp: EmployeeCreate,
    db: Session = Depends(get_db),
    admin: Employee = Depends(get_current_employee)
):
    """Manually add a single employee."""
    existing = db.query(Employee).filter(Employee.name.ilike(emp.name)).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"An employee named '{emp.name}' already exists")

    employee = Employee(name=emp.name, department=emp.department, role=emp.role, email=emp.email, pin=emp.pin)
    db.add(employee)
    db.commit()
    db.refresh(employee)

    return EmployeeResponse(
        id=employee.id,
        name=employee.name,
        department=employee.department,
        role=employee.role,
        email=employee.email,
        pin=employee.pin
    )

@router.get("/list")
def list_employees(
    db: Session = Depends(get_db),
    admin: Employee = Depends(get_current_employee)
):
    """List all employees."""
    employees = db.query(Employee).all()
    return [
        EmployeeResponse(
            id=e.id, name=e.name, department=e.department, role=e.role, email=e.email, pin=e.pin
        ) for e in employees
    ]

@router.delete("/{employee_id}")
def delete_employee(
    employee_id: int,
    db: Session = Depends(get_db),
    admin: Employee = Depends(get_current_employee)
):
    """Delete an employee."""
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    db.delete(employee)
    db.commit()

    return {"message": f"Employee {employee.name} deleted"}

@router.put("/{employee_id}")
def update_employee(
    employee_id: int,
    emp: EmployeeCreate,
    db: Session = Depends(get_db),
    admin: Employee = Depends(get_current_employee)
):
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    employee.name = emp.name
    employee.department = emp.department
    employee.role = emp.role
    employee.email = emp.email
    employee.pin = emp.pin if emp.pin is not None else employee.pin
    db.commit()
    db.refresh(employee)
    return EmployeeResponse(
        id=employee.id,
        name=employee.name,
        department=employee.department,
        role=employee.role,
        email=employee.email,
        pin=employee.pin
    )
