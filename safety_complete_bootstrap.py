#!/usr/bin/env python3
"""
Complete Safety Observations Project Bootstrap
Creates all files with correct content in one go
Run: python bootstrap_complete.py
"""

import os
from pathlib import Path

# Project root
ROOT = Path.cwd()

# File structure with content
FILES = {
    "requirements.txt": """fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
pydantic==2.5.0
pydantic-settings==2.1.0
jinja2==3.1.2
python-multipart==0.0.6
pdfplumber==0.10.3
aiofiles==23.2.1
python-dotenv==1.0.0
geopy==2.3.0
""",
    
    "run.py": """import uvicorn
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

if __name__ == "__main__":
    print('''
    ╔════════════════════════════════════════════╗
    ║  Safety Observations - Local Demo Server   ║
    ║  Starting on http://127.0.0.1:8000         ║
    ║  API Docs: http://127.0.0.1:8000/docs     ║
    ╚════════════════════════════════════════════╝
    ''')
    
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )
""",

    "init_db.py": """from app.database import engine, Base, SessionLocal
from app.models import Facility
from pathlib import Path

def init_db():
    Base.metadata.create_all(bind=engine)
    
    Path("uploads/observations").mkdir(parents=True, exist_ok=True)
    Path("uploads/walkarounds").mkdir(parents=True, exist_ok=True)
    Path("app/templates").mkdir(parents=True, exist_ok=True)
    Path("app/static").mkdir(parents=True, exist_ok=True)
    
    db = SessionLocal()
    
    facility = db.query(Facility).first()
    if not facility:
        facility = Facility(
            name="Main Facility",
            latitude=32.9321,
            longitude=-85.9618,
            radius_miles=2.0
        )
        db.add(facility)
        db.commit()
        print("✓ Default facility created at Alexander City, AL (32.9321, -85.9618)")
    else:
        print("✓ Facility already exists")
    
    db.close()
    print("✓ Database initialized")
    print("✓ Upload directories created")

if __name__ == "__main__":
    init_db()
""",

    "app/__init__.py": "# Safety Observations Application Package\n__version__ = '1.0.0'\n",
    
    "app/database.py": """from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "sqlite:///./safety.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()
""",

    "app/models.py": """from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class Employee(Base):
    __tablename__ = "employees"
    
    id = Column(Integer, primary_key=True, index=True)
    badge = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    department = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    observations = relationship("Observation", back_populates="employee")
    walkaround_submissions = relationship("WalkaroundSubmission", back_populates="employee")

class Facility(Base):
    __tablename__ = "facilities"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    radius_miles = Column(Float, default=2.0)
    created_at = Column(DateTime, default=datetime.utcnow)

class ObservationForm(Base):
    __tablename__ = "observation_forms"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    questions = relationship("ObservationQuestion", back_populates="form", cascade="all, delete-orphan")
    observations = relationship("Observation", back_populates="form")

class ObservationQuestion(Base):
    __tablename__ = "observation_questions"
    
    id = Column(Integer, primary_key=True, index=True)
    form_id = Column(Integer, ForeignKey("observation_forms.id"), nullable=False)
    text = Column(String, nullable=False)
    question_type = Column(String, default="text")
    required = Column(Boolean, default=False)
    order = Column(Integer, default=0)
    active = Column(Boolean, default=True)
    
    form = relationship("ObservationForm", back_populates="questions")

class Observation(Base):
    __tablename__ = "observations"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    form_id = Column(Integer, ForeignKey("observation_forms.id"), nullable=False)
    
    location_description = Column(String, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    responses = Column(JSON, nullable=True)
    photo_path = Column(String, nullable=True)
    video_path = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    employee = relationship("Employee", back_populates="observations")
    form = relationship("ObservationForm", back_populates="observations")

class WalkaroundForm(Base):
    __tablename__ = "walkaround_forms"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    pdf_path = Column(String, nullable=True)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    sections = relationship("WalkaroundSection", back_populates="form", cascade="all, delete-orphan")
    submissions = relationship("WalkaroundSubmission", back_populates="form")

class WalkaroundSection(Base):
    __tablename__ = "walkaround_sections"
    
    id = Column(Integer, primary_key=True, index=True)
    form_id = Column(Integer, ForeignKey("walkaround_forms.id"), nullable=False)
    name = Column(String, nullable=False)
    order = Column(Integer, default=0)
    active = Column(Boolean, default=True)
    
    form = relationship("WalkaroundForm", back_populates="sections")
    questions = relationship("WalkaroundQuestion", back_populates="section", cascade="all, delete-orphan")

class WalkaroundQuestion(Base):
    __tablename__ = "walkaround_questions"
    
    id = Column(Integer, primary_key=True, index=True)
    section_id = Column(Integer, ForeignKey("walkaround_sections.id"), nullable=False)
    text = Column(String, nullable=False)
    question_type = Column(String, default="pass_fail")
    order = Column(Integer, default=0)
    active = Column(Boolean, default=True)
    
    section = relationship("WalkaroundSection", back_populates="questions")

class WalkaroundSubmission(Base):
    __tablename__ = "walkaround_submissions"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    form_id = Column(Integer, ForeignKey("walkaround_forms.id"), nullable=False)
    
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    responses = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    employee = relationship("Employee", back_populates="walkaround_submissions")
    form = relationship("WalkaroundForm", back_populates="submissions")
""",

    "app/main.py": """from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os
from pathlib import Path

from app.routers import admin_auth, admin_users, admin_observations, admin_walkarounds
from app.database import engine, Base

Base.metadata.create_all(bind=engine)

Path("uploads/observations").mkdir(parents=True, exist_ok=True)
Path("uploads/walkarounds").mkdir(parents=True, exist_ok=True)
Path("app/templates").mkdir(parents=True, exist_ok=True)

app = FastAPI(title="Safety Observations", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(admin_auth.router, prefix="/api", tags=["auth"])
app.include_router(admin_users.router, prefix="/api", tags=["users"])
app.include_router(admin_observations.router, prefix="/api", tags=["observations"])
app.include_router(admin_walkarounds.router, prefix="/api", tags=["walkarounds"])

if os.path.exists("app/static"):
    app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/")
def root():
    return {"message": "Safety Observations API running."}

@app.get("/health")
def health():
    return {"status": "healthy"}
""",

    "app/routers/__init__.py": "# Routers package",
    
    "app/routers/admin_auth.py": """from fastapi import APIRouter, HTTPException, Request, Response, Depends
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

sessions = {}

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_employee(request: Request, db: Session = Depends(get_db)):
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
        content='{{"success": true, "message": "Login successful", "employee_name": "{}"}}'.format(employee.name),
        media_type="application/json"
    )
    response.set_cookie("session_token", token, httponly=True, max_age=43200)
    return response

@router.post("/logout")
def logout(request: Request):
    token = request.cookies.get("session_token")
    if token and token in sessions:
        del sessions[token]
    
    response = Response(content='{"success": true, "message": "Logged out"}', media_type="application/json")
    response.delete_cookie("session_token")
    return response

@router.get("/me")
def get_current_user(employee: Employee = Depends(get_current_employee)):
    return {
        "id": employee.id,
        "badge": employee.badge,
        "name": employee.name,
        "department": employee.department
    }
""",

    "app/routers/admin_users.py": """from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
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
    contents = await file.read()
    content_str = contents.decode('utf-8')
    
    csv_reader = csv.reader(io.StringIO(content_str))
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
            
            existing = db.query(Employee).filter(Employee.badge == badge).first()
            if existing:
                duplicates.append({"row": idx, "badge": badge, "name": name})
                skipped += 1
                continue
            
            employee = Employee(badge=badge, name=name, department=department)
            db.add(employee)
            imported += 1
        
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
    existing = db.query(Employee).filter(Employee.badge == emp.badge).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Badge {emp.badge} already exists")
    
    employee = Employee(badge=emp.badge, name=emp.name, department=emp.department)
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
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    db.delete(employee)
    db.commit()
    
    return {"message": f"Employee {employee.name} deleted"}
""",

    "app/routers/admin_observations.py": """from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List

from app.database import SessionLocal
from app.models import ObservationForm, ObservationQuestion
from app.routers.admin_auth import get_current_employee

router = APIRouter(prefix="/observations/forms", tags=["Observations"])

class QuestionCreate(BaseModel):
    text: str
    question_type: str = "text"
    required: bool = False
    order: int = 0

class QuestionResponse(BaseModel):
    id: int
    text: str
    question_type: str
    required: bool
    order: int

class ObservationFormCreate(BaseModel):
    name: str
    description: str = None

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/")
def create_form(
    form_data: ObservationFormCreate,
    db: Session = Depends(get_db),
    admin = Depends(get_current_employee)
):
    form = ObservationForm(name=form_data.name, description=form_data.description)
    db.add(form)
    db.commit()
    db.refresh(form)
    
    return {"id": form.id, "name": form.name, "message": "Form created"}

@router.get("/")
def list_forms(
    db: Session = Depends(get_db),
    admin = Depends(get_current_employee)
):
    forms = db.query(ObservationForm).all()
    return [
        {
            "id": f.id,
            "name": f.name,
            "description": f.description,
            "active": f.active,
            "question_count": len(f.questions)
        } for f in forms
    ]

@router.get("/{form_id}")
def get_form(
    form_id: int,
    db: Session = Depends(get_db),
    admin = Depends(get_current_employee)
):
    form = db.query(ObservationForm).filter(ObservationForm.id == form_id).first()
    if not form:
        raise HTTPException(status_code=404, detail="Form not found")
    
    return {
        "id": form.id,
        "name": form.name,
        "description": form.description,
        "active": form.active,
        "questions": [
            {
                "id": q.id,
                "text": q.text,
                "question_type": q.question_type,
                "required": q.required,
                "order": q.order
            } for q in form.questions
        ]
    }

@router.post("/{form_id}/questions")
def add_question(
    form_id: int,
    question: QuestionCreate,
    db: Session = Depends(get_db),
    admin = Depends(get_current_employee)
):
    form = db.query(ObservationForm).filter(ObservationForm.id == form_id).first()
    if not form:
        raise HTTPException(status_code=404, detail="Form not found")
    
    q = ObservationQuestion(
        form_id=form_id,
        text=question.text,
        question_type=question.question_type,
        required=question.required,
        order=question.order
    )
    db.add(q)
    db.commit()
    db.refresh(q)
    
    return {"id": q.id, "text": q.text}

@router.delete("/{form_id}/questions/{question_id}")
def delete_question(
    form_id: int,
    question_id: int,
    db: Session = Depends(get_db),
    admin = Depends(get_current_employee)
):
    q = db.query(ObservationQuestion).filter(
        ObservationQuestion.id == question_id,
        ObservationQuestion.form_id == form_id
    ).first()
    
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")
    
    db.delete(q)
    db.commit()
    
    return {"message": "Question deleted"}
""",

    "app/routers/admin_walkarounds.py": """from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
from pathlib import Path

from app.database import SessionLocal
from app.models import WalkaroundForm, WalkaroundSection, WalkaroundQuestion
from app.routers.admin_auth import get_current_employee
from app.utils.pdf_ocr import extract_text_from_pdf

router = APIRouter(prefix="/walkarounds", tags=["Walkarounds"])

class QuestionCreate(BaseModel):
    text: str
    question_type: str = "pass_fail"
    order: int = 0

class SectionCreate(BaseModel):
    name: str
    order: int = 0

class WalkaroundFormCreate(BaseModel):
    name: str
    description: str = None

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/upload-pdf")
async def upload_pdf(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    admin = Depends(get_current_employee)
):
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="File must be PDF")
    
    upload_dir = Path("uploads/walkarounds")
    upload_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = upload_dir / file.filename
    
    with open(pdf_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    try:
        extracted_data = extract_text_from_pdf(str(pdf_path))
        return {"sections": extracted_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF extraction failed: {str(e)}")

@router.post("/")
def create_form(
    form_data: WalkaroundFormCreate,
    db: Session = Depends(get_db),
    admin = Depends(get_current_employee)
):
    form = WalkaroundForm(name=form_data.name, description=form_data.description)
    db.add(form)
    db.commit()
    db.refresh(form)
    
    return {"id": form.id, "name": form.name, "message": "Form created"}

@router.get("/")
def list_forms(
    db: Session = Depends(get_db),
    admin = Depends(get_current_employee)
):
    forms = db.query(WalkaroundForm).all()
    return [
        {
            "id": f.id,
            "name": f.name,
            "description": f.description,
            "active": f.active,
            "section_count": len(f.sections)
        } for f in forms
    ]

@router.get("/{form_id}")
def get_form(
    form_id: int,
    db: Session = Depends(get_db),
    admin = Depends(get_current_employee)
):
    form = db.query(WalkaroundForm).filter(WalkaroundForm.id == form_id).first()
    if not form:
        raise HTTPException(status_code=404, detail="Form not found")
    
    return {
        "id": form.id,
        "name": form.name,
        "sections": [
            {
                "id": s.id,
                "name": s.name,
                "questions": [
                    {
                        "id": q.id,
                        "text": q.text,
                        "question_type": q.question_type
                    } for q in s.questions
                ]
            } for s in form.sections
        ]
    }

@router.post("/{form_id}/sections")
def add_section(
    form_id: int,
    section: SectionCreate,
    db: Session = Depends(get_db),
    admin = Depends(get_current_employee)
):
    form = db.query(WalkaroundForm).filter(WalkaroundForm.id == form_id).first()
    if not form:
        raise HTTPException(status_code=404, detail="Form not found")
    
    s = WalkaroundSection(form_id=form_id, name=section.name, order=section.order)
    db.add(s)
    db.commit()
    db.refresh(s)
    
    return {"id": s.id, "name": s.name}

@router.post("/{form_id}/sections/{section_id}/questions")
def add_question(
    form_id: int,
    section_id: int,
    question: QuestionCreate,
    db: Session = Depends(get_db),
    admin = Depends(get_current_employee)
):
    section = db.query(WalkaroundSection).filter(
        WalkaroundSection.id == section_id,
        WalkaroundSection.form_id == form_id
    ).first()
    
    if not section:
        raise HTTPException(status_code=404, detail="Section not found")
    
    q = WalkaroundQuestion(
        section_id=section_id,
        text=question.text,
        question_type=question.question_type,
        order=question.order
    )
    db.add(q)
    db.commit()
    db.refresh(q)
    
    return {"id": q.id, "text": q.text}
""",

    "app/utils/__init__.py": "# Utilities package",
    
    "app/utils/geo.py": """from math import radians, cos, sin, asin, sqrt

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    
    miles = 3959 * c
    
    return round(miles, 2)
""",

    "app/utils/pdf_ocr.py": """import pdfplumber
from typing import List, Dict

def extract_text_from_pdf(pdf_path: str) -> List[Dict]:
    sections = []
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                text = page.extract_text()
                lines = text.split('\\n')
                
                current_section = None
                
                for line in lines:
                    stripped = line.strip()
                    
                    if not stripped:
                        continue
                    
                    if stripped.isupper() and len(stripped) > 3:
                        if current_section:
                            sections.append(current_section)
                        
                        current_section = {
                            "name": stripped,
                            "order": len(sections),
                            "questions": []
                        }
                    
                    elif current_section and (
                        "□" in stripped or "☐" in stripped or 
                        stripped.startswith("•") or 
                        stripped.startswith("-") or
                        stripped[0].isdigit() or
                        "?" in stripped
                    ):
                        question_text = stripped.replace("□", "").replace("☐", "").replace("•", "").replace("-", "").strip()
                        
                        if question_text and question_text[0].isdigit():
                            question_text = question_text.split(".", 1)[-1].strip()
                        
                        if question_text:
                            current_section["questions"].append({
                                "text": question_text,
                                "question_type": "pass_fail",
                                "order": len(current_section["questions"])
                            })
                
                if current_section:
                    sections.append(current_section)
        
        return sections if sections else [
            {
                "name": "General",
                "order": 0,
                "questions": [{"text": "Sample question - please edit", "question_type": "pass_fail", "order": 0}]
            }
        ]
    
    except Exception as e:
        return [
            {
                "name": "Section 1",
                "order": 0,
                "questions": [
                    {
                        "text": f"Error extracting PDF: {str(e)}. Please manually add questions.",
                        "question_type": "text",
                        "order": 0
                    }
                ]
            }
        ]
"""
}

def create_all_files():
    """Create all project files"""
    for filepath, content in FILES.items():
        path = ROOT / filepath
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✓ Created {filepath}")
    
    print("\n✓ All files created successfully!")
    print("\nNext steps:")
    print("1. pip install -r requirements.txt")
    print("2. python init_db.py")
    print("3. python run.py")
    print("\nThen visit: http://127.0.0.1:8000/docs")

if __name__ == "__main__":
    create_all_files()
