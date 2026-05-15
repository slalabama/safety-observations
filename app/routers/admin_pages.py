from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["Admin Pages"])
templates = Jinja2Templates(directory="app/templates")

@router.get("/admin/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.get("/admin/", response_class=HTMLResponse)
def dashboard_page(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@router.get("/admin/users", response_class=HTMLResponse)
def users_page(request: Request):
    return templates.TemplateResponse("admin_users_page.html", {"request": request})

@router.get("/admin/observations", response_class=HTMLResponse)
def observations_page(request: Request):
    return templates.TemplateResponse("admin_observations_page.html", {"request": request})

@router.get("/admin/walkarounds", response_class=HTMLResponse)
def walkarounds_page(request: Request):
    return templates.TemplateResponse("admin_walkarounds_page.html", {"request": request})
@router.get("/admin/submissions", response_class=HTMLResponse)
def submissions_page(request: Request):
    return templates.TemplateResponse("admin_submissions_page.html", {"request": request})

@router.get("/observe", response_class=HTMLResponse)
def observe_page(request: Request):
    return templates.TemplateResponse("employee_observe.html", {"request": request})

@router.get("/walkaround", response_class=HTMLResponse)
def walkaround_page(request: Request):
    return templates.TemplateResponse("employee_walkaround.html", {"request": request})
