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
    Import employees from CSV. Format: name, department, role, email
    Skips duplicates by name.
    """
    contents = await file.read()
    content_str = contents.decode('utf-8')

    sample = content_str[:500]
    delimiter = '\t' if '\t' in sample else ','
    csv_reader = csv.reader(io.StringIO(content_str), delimiter=delimiter)
    rows = list(csv_reader)

    imported = 0
    skipped = 0
    duplicates = []

    for idx, row in enumerate(rows, 1):
        if not row:
            continue
        # Skip header row
        if row[0].strip().lower() in ("name", "first name", "full name"):
            continue

        try:
            name = row[0].strip()
            department = row[1].strip() if len(row) > 1 and row[1].strip() else None
            role = row[2].strip().lower() if len(row) > 2 and row[2].strip() else "basic"
            email = row[3].strip() if len(row) > 3 and row[3].strip() else None

            if not name:
                continue

            existing = db.query(Employee).filter(Employee.name.ilike(name)).first()
            if existing:
                duplicates.append({"row": idx, "name": name})
                skipped += 1
                continue

            employee = Employee(name=name, department=department, role=role, email=email)
            db.add(employee)
            try:
                db.flush()
                imported += 1
            except Exception:
                db.rollback()
                duplicates.append({"row": idx, "name": name})
                skipped += 1

        except Exception as e:
            skipped += 1
            duplicates.append({"row": idx, "error": str(e)})

    db.commit()

    return CSVImportResponse(
        total=len(rows) - 1,
        imported=imported,
        skipped=skipped,
        duplicates=duplicates
    )

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
