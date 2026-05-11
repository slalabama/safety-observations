from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
import os
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

class OCRResult(BaseModel):
    sections: List[dict]

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
    """
    Upload PDF form and extract text for OCR.
    Returns structured data that admin can review/edit before creating form.
    """
    
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="File must be PDF")
    
    # Save PDF temporarily
    upload_dir = Path("uploads/walkarounds")
    upload_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = upload_dir / file.filename
    
    with open(pdf_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    # Extract text
    try:
        extracted_data = extract_text_from_pdf(str(pdf_path))
        return OCRResult(sections=extracted_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF extraction failed: {str(e)}")

@router.post("/create-from-ocr")
def create_form_from_ocr(
    form_data: dict,
    db: Session = Depends(get_db),
    admin = Depends(get_current_employee)
):
    """
    Create walkaround form from OCR data (admin-reviewed).
    """
    
    form = WalkaroundForm(name=form_data.get("name"), description=form_data.get("description"))
    db.add(form)
    db.flush()
    
    for sec_idx, section_data in enumerate(form_data.get("sections", [])):
        section = WalkaroundSection(
            form_id=form.id,
            name=section_data.get("name"),
            order=sec_idx
        )
        db.add(section)
        db.flush()
        
        for q_idx, question_data in enumerate(section_data.get("questions", [])):
            question = WalkaroundQuestion(
                section_id=section.id,
                text=question_data.get("text"),
                question_type=question_data.get("question_type", "pass_fail"),
                order=q_idx
            )
            db.add(question)
    
    db.commit()
    db.refresh(form)
    
    return {"id": form.id, "name": form.name, "message": "Form created from OCR"}

@router.post("/")
def create_form(
    form_data: WalkaroundFormCreate,
    db: Session = Depends(get_db),
    admin = Depends(get_current_employee)
):
    """Create a new walkaround form manually."""
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
    """List all walkaround forms."""
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
    """Get a walkaround form with sections and questions."""
    form = db.query(WalkaroundForm).filter(WalkaroundForm.id == form_id).first()
    if not form:
        raise HTTPException(status_code=404, detail="Form not found")
    
    return {
        "id": form.id,
        "name": form.name,
        "description": form.description,
        "active": form.active,
        "sections": [
            {
                "id": s.id,
                "name": s.name,
                "order": s.order,
                "questions": [
                    {
                        "id": q.id,
                        "text": q.text,
                        "question_type": q.question_type,
                        "order": q.order
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
    """Add a section to a form."""
    form = db.query(WalkaroundForm).filter(WalkaroundForm.id == form_id).first()
    if not form:
        raise HTTPException(status_code=404, detail="Form not found")
    
    s = WalkaroundSection(form_id=form_id, name=section.name, order=section.order)
    db.add(s)
    db.commit()
    db.refresh(s)
    
    return {"id": s.id, "name": s.name, "order": s.order}

@router.post("/{form_id}/sections/{section_id}/questions")
def add_question(
    form_id: int,
    section_id: int,
    question: QuestionCreate,
    db: Session = Depends(get_db),
    admin = Depends(get_current_employee)
):
    """Add a question to a section."""
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
    
    return {"id": q.id, "text": q.text, "question_type": q.question_type}
@router.delete("/{form_id}/sections/{section_id}/questions/{question_id}")
def delete_question(form_id: int, section_id: int, question_id: int, db: Session = Depends(get_db), admin = Depends(get_current_employee)):
    q = db.query(WalkaroundQuestion).filter(WalkaroundQuestion.id == question_id, WalkaroundQuestion.section_id == section_id).first()
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")
    db.delete(q)
    db.commit()
    return {"message": "Question deleted"}

@router.put("/{form_id}/sections/{section_id}/questions/{question_id}")
def update_question(form_id: int, section_id: int, question_id: int, question: QuestionCreate, db: Session = Depends(get_db), admin = Depends(get_current_employee)):
    q = db.query(WalkaroundQuestion).filter(WalkaroundQuestion.id == question_id, WalkaroundQuestion.section_id == section_id).first()
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")
    q.text = question.text
    q.question_type = question.question_type
    db.commit()
    db.refresh(q)
    return {"id": q.id, "text": q.text, "question_type": q.question_type}
