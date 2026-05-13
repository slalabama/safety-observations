from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
import os
from pathlib import Path

from app.routers import admin_auth, admin_users, admin_observations, admin_walkarounds, admin_pages, setup, email_test
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

if os.path.exists("app/static"):
    app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/")
def root():
    return RedirectResponse(url="/admin/login")

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

