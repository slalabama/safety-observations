content = open('app/routers/admin_observations.py','r',encoding='utf-8').read()
new_endpoint = '''
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
'''
content = content + new_endpoint
open('app/routers/admin_observations.py','w',encoding='utf-8').write(content)
print('Done!')
