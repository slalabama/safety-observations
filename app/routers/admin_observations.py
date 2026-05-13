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
    """Incident report submission. Requires session cookie set by observe-login."""
    import base64
    from datetime import datetime
    from app.models import Observation, Employee, SessionRecord

    MAX_BYTES = 10 * 1024 * 1024  # 10 MB

    form = await request.form()
    incident_type = (form.get("incident_type") or "").strip()
    description   = (form.get("description") or "").strip()
    badge         = (form.get("badge") or "").strip()

    if not incident_type:
        raise HTTPException(status_code=400, detail="Type of Incident is required.")
    if not description:
        raise HTTPException(status_code=400, detail="Description is required.")

    # Identify employee: badge from form, else session cookie
    employee = None
    if badge:
        employee = db.query(Employee).filter(Employee.badge == badge).first()
    if not employee:
        token = request.cookies.get("session_token")
        if token:
            sr = db.query(SessionRecord).filter(SessionRecord.id == token).first()
            if sr and sr.expires_at > datetime.utcnow():
                employee = sr.employee
    if not employee:
        raise HTTPException(status_code=401, detail="Please log in again.")

    photo_data = None
    video_data = None

    photo = form.get("photo")
    if photo and hasattr(photo, "filename") and photo.filename:
        content = await photo.read()
        if len(content) > MAX_BYTES:
            raise HTTPException(status_code=413, detail="Photo exceeds 10 MB limit.")
        photo_data = base64.b64encode(content).decode("ascii")

    video = form.get("video")
    if video and hasattr(video, "filename") and video.filename:
        content = await video.read()
        if len(content) > MAX_BYTES:
            raise HTTPException(status_code=413, detail="Video exceeds 10 MB limit.")
        video_data = base64.b64encode(content).decode("ascii")

    record = Observation(
        employee_id=employee.id,
        form_id=0,                          # no template form used
        incident_type=incident_type,
        description=description,
        photo_data=photo_data,
        video_data=video_data,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return {
        "success": True,
        "observation_id": record.id,
        "employee_name": employee.name,
        "message": "Report submitted successfully."
    }

