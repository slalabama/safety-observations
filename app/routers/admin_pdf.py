"""
PDF download endpoints for safety submissions.

Both routes are admin-only. They build a Safety 1st-branded PDF on the fly
from current DB state and stream it back as application/pdf. No caching —
edits to the underlying data are reflected immediately on the next hit.

Routes (mounted under /api by main.py):
    GET /api/observations/{obs_id}/pdf
    GET /api/walkarounds/submissions/{sub_id}/pdf
"""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response

from app.database import SessionLocal
from app.models import (
    Employee,
    Observation,
    SessionRecord,
    WalkaroundForm,
    WalkaroundSection,
    WalkaroundQuestion,
    WalkaroundSubmission,
)
from app.utils.pdf_builder import (
    build_observation_pdf,
    build_walkaround_pdf,
)

router = APIRouter()


# ---------- auth ----------

def require_admin(request: Request) -> Employee:
    """
    Admin-only gate. Reads the session cookie, looks up SessionRecord,
    confirms the employee is active and role='admin'.

    NOTE: The cookie name varies by implementation. We check several
    common names; if none of these match what admin_auth.py is setting,
    add the right name to the list below.
    """
    token = (
        request.cookies.get("session_token")
        or request.cookies.get("session")
        or request.cookies.get("session_id")
        or request.cookies.get("auth_token")
    )
    if not token:
        raise HTTPException(status_code=401, detail="not authenticated")

    db = SessionLocal()
    try:
        rec = db.query(SessionRecord).filter(SessionRecord.id == token).first()
        if not rec:
            raise HTTPException(status_code=401, detail="session not found")
        if rec.expires_at and rec.expires_at < datetime.utcnow():
            raise HTTPException(status_code=401, detail="session expired")

        emp = db.query(Employee).filter(Employee.id == rec.employee_id).first()
        if not emp:
            raise HTTPException(status_code=401, detail="employee not found")
        if emp.status and emp.status != "active":
            raise HTTPException(status_code=403, detail="user inactive")
        if emp.role != "admin":
            raise HTTPException(status_code=403, detail="admin only")

        # Detach so we can return the object after the session closes
        db.expunge(emp)
        return emp
    finally:
        db.close()


# ---------- dict serializers ----------

def _employee_dict(emp: Optional[Employee]) -> dict:
    if not emp:
        return {"name": "Unknown", "badge": "\u2014", "department": "\u2014", "role": None}
    return {
        "id":         emp.id,
        "name":       emp.name,
        "badge":      emp.badge,
        "department": emp.department,
        "role":       emp.role,
        "email":      emp.email,
    }


def _observation_dict(obs: Observation) -> dict:
    return {
        "id":                   obs.id,
        "incident_type":        obs.incident_type,
        "description":          obs.description,
        "location_description": obs.location_description,
        "created_at":           obs.created_at,
        "photo_data":           obs.photo_data,
        "video_data":           obs.video_data,
    }


def _walkaround_dict(sub: WalkaroundSubmission) -> dict:
    return {
        "id":         sub.id,
        "form_id":    sub.form_id,
        "latitude":   sub.latitude,
        "longitude":  sub.longitude,
        "responses":  sub.responses or {},
        "photo_data": sub.photo_data,
        "video_data": sub.video_data,
        "created_at": sub.created_at,
    }


def _form_with_structure(db, form_id: int) -> dict:
    """Load a walkaround form with its active sections + questions."""
    form = db.query(WalkaroundForm).filter(WalkaroundForm.id == form_id).first()
    if not form:
        return {"name": "Unknown Form", "description": "", "sections": []}

    sections_out = []
    sections = (
        db.query(WalkaroundSection)
          .filter(
              WalkaroundSection.form_id == form.id,
              WalkaroundSection.active == True,  # noqa: E712
          )
          .order_by(WalkaroundSection.order)
          .all()
    )
    for sec in sections:
        qs = (
            db.query(WalkaroundQuestion)
              .filter(
                  WalkaroundQuestion.section_id == sec.id,
                  WalkaroundQuestion.active == True,  # noqa: E712
              )
              .order_by(WalkaroundQuestion.order)
              .all()
        )
        sections_out.append({
            "id":   sec.id,
            "name": sec.name,
            "questions": [
                {"id": q.id, "text": q.text, "question_type": q.question_type}
                for q in qs
            ],
        })

    return {
        "id":          form.id,
        "name":        form.name,
        "description": form.description,
        "sections":    sections_out,
    }


# ---------- routes ----------

@router.get("/observations/{obs_id}/pdf")
def observation_pdf(obs_id: int, admin: Employee = Depends(require_admin)):
    db = SessionLocal()
    try:
        obs = db.query(Observation).filter(Observation.id == obs_id).first()
        if not obs:
            raise HTTPException(status_code=404, detail="observation not found")
        emp = db.query(Employee).filter(Employee.id == obs.employee_id).first()
        pdf_bytes = build_observation_pdf(_observation_dict(obs), _employee_dict(emp))
    finally:
        db.close()

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'inline; filename="observation-{obs_id}.pdf"',
            "Cache-Control": "no-store",
        },
    )


@router.get("/walkarounds/submissions/{sub_id}/pdf")
def walkaround_pdf(sub_id: int, admin: Employee = Depends(require_admin)):
    db = SessionLocal()
    try:
        sub = db.query(WalkaroundSubmission).filter(WalkaroundSubmission.id == sub_id).first()
        if not sub:
            raise HTTPException(status_code=404, detail="submission not found")
        emp = db.query(Employee).filter(Employee.id == sub.employee_id).first()
        form_dict = _form_with_structure(db, sub.form_id)
        pdf_bytes = build_walkaround_pdf(_walkaround_dict(sub), form_dict, _employee_dict(emp))
    finally:
        db.close()

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'inline; filename="walkaround-{sub_id}.pdf"',
            "Cache-Control": "no-store",
        },
    )
