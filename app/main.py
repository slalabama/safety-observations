from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
import os
from pathlib import Path

from app.routers import admin_auth, admin_users, admin_observations, admin_walkarounds, admin_pages
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

if os.path.exists("app/static"):
    app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/")
def root():
    return RedirectResponse(url="/admin/login")

@app.get("/health")
def health():
    return {"status": "healthy"}
