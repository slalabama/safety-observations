from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Request
from sqlalchemy.orm import Session
import csv
import io
import re
from pydantic import BaseModel
from typing import Optional

from app.database import SessionLocal
from app.models import Employee
from app.routers.admin_auth import get_current_employee

router = APIRouter(prefix="/users", tags=["Users"])


# ---------- schemas ----------

class EmployeeCreate(BaseModel):
    name: str
    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    last_name: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    shift: Optional[str] = None
    role: str = "basic"
    email: Optional[str] = None
    pin: Optional[str] = None


class EmployeeResponse(BaseModel):
    id: int
    badge: Optional[str] = None
    name: str
    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    last_name: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    shift: Optional[str] = None
    role: str = "basic"
    email: Optional[str] = None
    pin: Optional[str] = None


class CSVImportResponse(BaseModel):
    total: int
    imported: int
    skipped: int
    duplicates: list


# ---------- helpers ----------

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _normalize_header(h: str) -> str:
    """
    Normalize a CSV header for matching:
      'Position(US)' -> 'position'
      'Emp ID'       -> 'emp_id'
      'First Name'   -> 'first_name'
      'E-mail'       -> 'e_mail'   (then mapped to email below)
    """
    if not h:
        return ""
    # Strip parenthetical groups like (US), (UK), (1)
    h = re.sub(r"\([^)]*\)", "", h)
    h = h.strip().lower()
    # Collapse spaces, hyphens, dots, slashes into underscores
    h = re.sub(r"[\s\-\.\/]+", "_", h)
    # Collapse runs of underscores
    h = re.sub(r"_+", "_", h).strip("_")
    return h


# Header values that mean "this isn't a real row, skip it" — used to detect
# duplicate header rows that some exports include twice.
_HEADER_BADGE_VALUES = {"emp_id", "emp id", "employee_id", "employee id", "badge", "id"}


def _maybe_dewrap_csv(text: str) -> str:
    """
    Some exports wrap every row in outer quotes with doubled internal quotes,
    e.g.:
        "Name,First Name,Last Name"
        "Coltrain, Jack R.,""Jack"",Coltrain"
    In that format csv.DictReader sees a single column whose value is the
    entire row string, which breaks all field lookups. If we detect this
    format (every non-empty line starts and ends with a quote), strip one
    layer of quoting so the inner content parses normally. Leave standard
    CSVs untouched.
    """
    lines = text.splitlines()
    sample = [ln.strip() for ln in lines if ln.strip()]
    if not sample:
        return text
    # Only treat as outer-quoted if the first several lines all look that way
    head = sample[:5]
    if not all(ln.startswith('"') and ln.endswith('"') and len(ln) >= 2 for ln in head):
        return text

    out = []
    for ln in lines:
        s = ln.strip()
        if s.startswith('"') and s.endswith('"') and len(s) >= 2:
            inner = s[1:-1].replace('""', '"')
            out.append(inner)
        else:
            out.append(s)
    return "\n".join(out)


def _employee_to_response(e: Employee) -> EmployeeResponse:
    return EmployeeResponse(
        id=e.id,
        badge=e.badge,
        name=e.name,
        first_name=e.first_name,
        middle_name=getattr(e, "middle_name", None),
        last_name=e.last_name,
        department=e.department,
        position=getattr(e, "position", None),
        shift=getattr(e, "shift", None),
        role=e.role or "basic",
        email=e.email,
        pin=e.pin,
    )


# ---------- routes ----------

@router.post("/import-csv")
async def import_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    admin: Employee = Depends(get_current_employee),
):
    """
    Import employees from CSV.

    Accepted headers (case-insensitive, '(US)'-style suffixes ignored):
      Emp ID / badge          -> badge
      Name                    -> name (built from First+Middle+Last if blank)
      First Name / first      -> first_name
      Middle Name / middle    -> middle_name
      Last Name / last        -> last_name
      Position / Position(US) -> position
      Shift                   -> shift
      Department              -> department
      Role                    -> role
      Email                   -> email

    Match key is badge (unique). When a badge already exists, empty fields
    on the existing row get filled in from the CSV; existing non-empty
    values are never overwritten.
    """
    contents = await file.read()
    text = contents.decode("utf-8-sig")

    # Some exports wrap every row in outer quotes — unwrap if detected
    text = _maybe_dewrap_csv(text)

    # Sniff tab vs comma delimiter
    sample = text[:500]
    delim = "\t" if "\t" in sample else ","
    reader = csv.DictReader(io.StringIO(text), delimiter=delim)

    # Normalize headers once
    reader.fieldnames = [_normalize_header(h) for h in (reader.fieldnames or [])]

    imported = 0
    skipped = 0
    duplicates = []
    total = 0

    for idx, row in enumerate(reader, 1):
        total += 1
        try:
            badge    = (row.get("badge") or row.get("emp_id") or row.get("employee_id") or "").strip()
            name     = (row.get("name") or "").strip()
            first    = (row.get("first_name") or row.get("first") or "").strip()
            middle   = (row.get("middle_name") or row.get("middle") or "").strip()
            last     = (row.get("last_name") or row.get("last") or "").strip()
            position = (row.get("position") or "").strip() or None
            shift    = (row.get("shift") or "").strip() or None
            dept     = (row.get("department") or "").strip() or None
            role     = ((row.get("role") or "basic").strip().lower()) or "basic"
            email    = (row.get("email") or row.get("e_mail") or row.get("email_address") or "").strip() or None

            # Skip duplicate header rows that some exports include twice
            if badge.lower() in _HEADER_BADGE_VALUES:
                skipped += 1
                duplicates.append({"row": idx, "error": "duplicate header row, skipped"})
                continue

            # Build Name from First+Middle+Last when Name itself is blank
            if not name:
                name = " ".join(p for p in (first, middle, last) if p).strip()

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
                # Fill empty fields only — never overwrite existing data
                if first and not existing.first_name:
                    existing.first_name = first
                if middle and not getattr(existing, "middle_name", None):
                    existing.middle_name = middle
                if last and not existing.last_name:
                    existing.last_name = last
                if position and not getattr(existing, "position", None):
                    existing.position = position
                if shift and not getattr(existing, "shift", None):
                    existing.shift = shift
                if dept and not existing.department:
                    existing.department = dept
                duplicates.append({"row": idx, "name": name, "badge": badge})
                skipped += 1
                continue

            db.add(Employee(
                badge=badge,
                name=name,
                first_name=first or None,
                middle_name=middle or None,
                last_name=last or None,
                position=position,
                shift=shift,
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
    admin: Employee = Depends(get_current_employee),
):
    """Manually add a single employee."""
    existing = db.query(Employee).filter(Employee.name.ilike(emp.name)).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"An employee named '{emp.name}' already exists")

    employee = Employee(
        name=emp.name,
        first_name=emp.first_name,
        middle_name=emp.middle_name,
        last_name=emp.last_name,
        department=emp.department,
        position=emp.position,
        shift=emp.shift,
        role=emp.role,
        email=emp.email,
        pin=emp.pin,
    )
    db.add(employee)
    db.commit()
    db.refresh(employee)
    return _employee_to_response(employee)


@router.get("/list")
def list_employees(
    db: Session = Depends(get_db),
    admin: Employee = Depends(get_current_employee),
):
    """List all employees."""
    employees = db.query(Employee).all()
    return [_employee_to_response(e) for e in employees]


@router.delete("/{employee_id}")
def delete_employee(
    employee_id: int,
    db: Session = Depends(get_db),
    admin: Employee = Depends(get_current_employee),
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
    admin: Employee = Depends(get_current_employee),
):
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    employee.name        = emp.name
    employee.first_name  = emp.first_name
    employee.middle_name = emp.middle_name
    employee.last_name   = emp.last_name
    employee.department  = emp.department
    employee.position    = emp.position
    employee.shift       = emp.shift
    employee.role        = emp.role
    employee.email       = emp.email
    if emp.pin is not None:
        employee.pin = emp.pin

    db.commit()
    db.refresh(employee)
    return _employee_to_response(employee)
