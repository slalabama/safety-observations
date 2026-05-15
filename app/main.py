from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, FileResponse
import os
from pathlib import Path

from app.routers import admin_auth, admin_users, admin_observations, admin_walkarounds, admin_pages, setup, email_test, dashboard, admin_pdf
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

# API routes
app.include_router(admin_auth.router, prefix="/api")
app.include_router(admin_users.router, prefix="/api")
app.include_router(admin_observations.router, prefix="/api")
app.include_router(admin_walkarounds.router, prefix="/api")

# HTML page routes
app.include_router(admin_pages.router)
app.include_router(setup.router)
app.include_router(email_test.router)
app.include_router(dashboard.router, prefix="/api")
app.include_router(admin_pdf.router, prefix="/api")

if os.path.exists("app/static"):
    app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/")
def root():
    return RedirectResponse(url="/admin/login")

@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return FileResponse("app/static/favicon.ico")

@app.get("/health")
def health():
    return {"status": "healthy"}

# --- Auto-migration: ensure pin column exists on employees ----------------
@app.on_event("startup")
def _ensure_pin_column():
    from sqlalchemy import text
    from app.database import engine
    try:
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE employees ADD COLUMN IF NOT EXISTS pin VARCHAR"))
            conn.execute(text("ALTER TABLE employees ADD COLUMN IF NOT EXISTS first_name VARCHAR"))
            conn.execute(text("ALTER TABLE employees ADD COLUMN IF NOT EXISTS last_name VARCHAR"))
            conn.commit()
            print("[startup] pin column ensured")
    except Exception as e:
        print(f"[startup] pin column migration failed: {e}")
# --------------------------------------------------------------------------


@app.on_event("startup")
def auto_seed_admins():
    """Re-seed admins automatically on every deploy."""
    try:
        from app.database import SessionLocal
        from app.routers.setup import run_setup
        db = SessionLocal()
        try:
            run_setup(db)
            print("[startup] auto_seed_admins complete")
        finally:
            db.close()
    except Exception as e:
        print(f"[startup] auto_seed_admins failed: {e}")

@app.on_event("startup")
def _ensure_observation_fields():
    from sqlalchemy import text
    from app.database import engine, Base
    from app.models import Observation, Employee, SessionRecord, Facility, ObservationForm, ObservationQuestion, WalkaroundForm, WalkaroundSection, WalkaroundQuestion, WalkaroundSubmission
    try:
        # First, create any missing tables (idempotent)
        Base.metadata.create_all(bind=engine)
        # Then add new columns to existing tables
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE observations ADD COLUMN IF NOT EXISTS incident_type VARCHAR"))
            conn.execute(text("ALTER TABLE observations ADD COLUMN IF NOT EXISTS description TEXT"))
            conn.execute(text("ALTER TABLE observations ADD COLUMN IF NOT EXISTS photo_data TEXT"))
            conn.execute(text("ALTER TABLE observations ADD COLUMN IF NOT EXISTS video_data TEXT"))
            conn.commit()
        print("[startup] observations table created and columns ensured")
    except Exception as e:
        print(f"[startup] observation migration failed: {e}")

@app.on_event("startup")
def _ensure_walkaround_submission_fields():
    from sqlalchemy import text
    from app.database import engine, Base
    try:
        Base.metadata.create_all(bind=engine)
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE walkaround_submissions ADD COLUMN IF NOT EXISTS photo_data TEXT"))
            conn.execute(text("ALTER TABLE walkaround_submissions ADD COLUMN IF NOT EXISTS video_data TEXT"))
            conn.commit()
        print("[startup] walkaround_submissions columns ensured")
    except Exception as e:
        print(f"[startup] walkaround_submissions migration failed: {e}")

