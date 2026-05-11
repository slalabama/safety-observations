from fastapi import APIRouter, HTTPException, Depends, Request, UploadFile, File
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

class ObservationFormUpdate(BaseModel):
    name: str = None
    description: str = None
    active: bool = None

class ObservationFormDetail(BaseModel):
    id: int
    name: str
    description: str
    active: bool
    questions: List[QuestionResponse]

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
    """Create a new observation form."""
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
    """List all observation forms."""
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
    """Get a specific observation form with all questions."""
    form = db.query(ObservationForm).filter(ObservationForm.id == form_id).first()
    if not form:
        raise HTTPException(status_code=404, detail="Form not found")
    
    return ObservationFormDetail(
        id=form.id,
        name=form.name,
        description=form.description,
        active=form.active,
        questions=[
            QuestionResponse(
                id=q.id,
                text=q.text,
                question_type=q.question_type,
                required=q.required,
                order=q.order
            ) for q in form.questions
        ]
    )

@router.post("/{form_id}/questions")
def add_question(
    form_id: int,
    question: QuestionCreate,
    db: Session = Depends(get_db),
    admin = Depends(get_current_employee)
):
    """Add a question to a form."""
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
    
    return QuestionResponse(
        id=q.id,
        text=q.text,
        question_type=q.question_type,
        required=q.required,
        order=q.order
    )

@router.put("/{form_id}/questions/{question_id}")
def update_question(
    form_id: int,
    question_id: int,
    question: QuestionCreate,
    db: Session = Depends(get_db),
    admin = Depends(get_current_employee)
):
    """Update a question."""
    q = db.query(ObservationQuestion).filter(
        ObservationQuestion.id == question_id,
        ObservationQuestion.form_id == form_id
    ).first()
    
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")
    
    q.text = question.text
    q.question_type = question.question_type
    q.required = question.required
    q.order = question.order
    
    db.commit()
    db.refresh(q)
    
    return QuestionResponse(
        id=q.id,
        text=q.text,
        question_type=q.question_type,
        required=q.required,
        order=q.order
    )

@router.delete("/{form_id}/questions/{question_id}")
def delete_question(
    form_id: int,
    question_id: int,
    db: Session = Depends(get_db),
    admin = Depends(get_current_employee)
):
    """Delete a question."""
    q = db.query(ObservationQuestion).filter(
        ObservationQuestion.id == question_id,
        ObservationQuestion.form_id == form_id
    ).first()
    
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")
    
    db.delete(q)
    db.commit()
    
    return {"message": "Question deleted"}
@router.post("/submit")
async def submit_observation(
    request: Request,
    db: Session = Depends(get_db)
):
    import json
    from app.models import Observation, Employee
    from fastapi import UploadFile
    from pathlib import Path
    import shutil

    form = await request.form()
    badge = form.get("badge")
    form_id = int(form.get("form_id", 0))
    location = form.get("location", "")
    responses = json.loads(form.get("responses", "{}"))

    employee = db.query(Employee).filter(Employee.badge == badge).first()
    if not employee:
        raise HTTPException(status_code=401, detail="Invalid badge")

    photo_path = None
    video_path = None

    photo = form.get("photo")
    if photo and hasattr(photo, "filename") and photo.filename:
        Path("uploads/observations").mkdir(parents=True, exist_ok=True)
        photo_path = f"uploads/observations/{badge}_{photo.filename}"
        with open(photo_path, "wb") as f:
            f.write(await photo.read())

    video = form.get("video")
    if video and hasattr(video, "filename") and video.filename:
        Path("uploads/observations").mkdir(parents=True, exist_ok=True)
        video_path = f"uploads/observations/{badge}_{video.filename}"
        with open(video_path, "wb") as f:
            f.write(await video.read())

    obs = Observation(
        employee_id=employee.id,
        form_id=form_id,
        location_description=location,
        responses=responses,
        photo_path=photo_path,
        video_path=video_path
    )
    db.add(obs)
    db.commit()

    # Email all admins
    admins = db.query(Employee).filter(Employee.role == "admin", Employee.email != None).all()
    admin_emails = [a.email for a in admins if a.email]

    if admin_emails:
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart

            msg = MIMEMultipart()
            msg["From"] = "hello@kixlogic.com"
            msg["To"] = ", ".join(admin_emails)
            msg["Subject"] = f"Safety Observation Submitted by {employee.name}"

            body = f"""
A new safety observation has been submitted.

Employee: {employee.name} (Badge: {badge})
Location: {location}
Form: {form_id}
Time: {obs.created_at}

Please log in to review: http://localhost:8000/admin/
            """
            msg.attach(MIMEText(body, "plain"))

            with smtplib.SMTP_SSL("smtp.bizmail.yahoo.com", 465) as server:
                server.login("hello@kixlogic.com", "your_password_here")
                server.sendmail("hello@kixlogic.com", admin_emails, msg.as_string())
        except Exception as e:
            print(f"Email failed: {e}")

    return {"success": True, "message": "Observation submitted successfully"}
