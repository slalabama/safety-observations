from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Request
from sqlalchemy.orm import Session
import csv
import io
from pydantic import BaseModel

from app.database import SessionLocal
from app.models import Employee
from app.routers.admin_auth import get_current_employee

router = APIRouter(prefix="/users", tags=["Users"])

class EmployeeCreate(BaseModel):
    badge: str
    name: str
    department: str = None
    role: str = "basic"
    email: str = None

class EmployeeResponse(BaseModel):
    id: int
    badge: str
    name: str
    department: str

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
    Import employees from CSV. Format: badge,name[,department]
    Returns report of imported/duplicated employees.
    """
    
    contents = await file.read()
    content_str = contents.decode('utf-8')
    
    # Auto-detect delimiter (tab or comma)
    sample = content_str[:500]
    delimiter = '\t' if '\t' in sample else ','
    csv_reader = csv.reader(io.StringIO(content_str), delimiter=delimiter)
    rows = list(csv_reader)
    
    imported = 0
    skipped = 0
    duplicates = []
    
    for idx, row in enumerate(rows, 1):
        if not row or row[0].strip() == "badge":
            continue
        
        try:
            badge = row[0].strip()
            name = row[1].strip()
            department = row[2].strip() if len(row) > 2 else None
            # Skip header rows
            if badge.lower() == 'badge' or not badge.isdigit() and not badge.replace('-','').isdigit():
                if not any(c.isdigit() for c in badge):
                    continue
            
            existing = db.query(Employee).filter(Employee.badge == badge).first()
            if existing:
                duplicates.append({"row": idx, "badge": badge, "name": name})
                skipped += 1
                continue
            
            employee = Employee(badge=badge, name=name, department=department)
            db.add(employee)
            try:
                db.flush()
                imported += 1
            except Exception:
                db.rollback()
                duplicates.append({"row": idx, "badge": badge, "name": name})
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
    
    existing = db.query(Employee).filter(Employee.badge == emp.badge).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Badge {emp.badge} already exists")
    
    employee = Employee(badge=emp.badge, name=emp.name, department=emp.department, role=emp.role, email=emp.email)
    db.add(employee)
    db.commit()
    db.refresh(employee)
    
    return EmployeeResponse(
        id=employee.id,
        badge=employee.badge,
        name=employee.name,
        department=employee.department
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
            id=e.id, badge=e.badge, name=e.name, department=e.department
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
    employee.badge = emp.badge
    employee.name = emp.name
    employee.department = emp.department
    employee.role = emp.role
    employee.email = emp.email
    db.commit()
    db.refresh(employee)
    return EmployeeResponse(id=employee.id, badge=employee.badge, name=employee.name, department=employee.department)
