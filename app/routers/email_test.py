"""
Email test endpoints.

GET /test-email           -> send to NOTIFY_EMAIL (or EMAIL_FROM if unset)
GET /test-email?to=<addr> -> send to a specific address
GET /test-email-debug     -> show SMTP config (password masked) without sending

Both endpoints always return JSON so we can see exactly what happened
instead of a generic 500.
"""
import os
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.utils.email_sender import send_email

router = APIRouter()


@router.get("/test-email")
def test_email(to: str | None = None):
    target = (
        to
        or os.environ.get("NOTIFY_EMAIL")
        or os.environ.get("EMAIL_FROM")
        or os.environ.get("SMTP_USER")
    )
    if not target:
        return JSONResponse(
            status_code=400,
            content={"ok": False, "detail": "no recipient: pass ?to=<addr> or set NOTIFY_EMAIL"},
        )

    ok, detail = send_email(
        to_addr=target,
        subject="Safety 1st — SMTP test",
        body="If you can read this, outbound mail from Railway is working.\n\n"
             "Sent by the Safety 1st test endpoint.",
    )

    return JSONResponse(
        status_code=200 if ok else 502,
        content={"ok": ok, "to": target, "detail": detail},
    )


@router.get("/test-email-debug")
def test_email_debug():
    """Inspect SMTP config without sending. Password is masked."""
    pwd = os.environ.get("SMTP_PASSWORD", "")
    return {
        "smtp_host":     os.environ.get("SMTP_HOST", ""),
        "smtp_port":     os.environ.get("SMTP_PORT", ""),
        "smtp_user":     os.environ.get("SMTP_USER", ""),
        "email_from":    os.environ.get("EMAIL_FROM", ""),
        "notify_email":  os.environ.get("NOTIFY_EMAIL", "(unset — falls back to EMAIL_FROM)"),
        "password_set":  bool(pwd),
        "password_len":  len(pwd),
    }
