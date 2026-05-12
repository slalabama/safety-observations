from fastapi import APIRouter, HTTPException
from app.utils.email_sender import send_email

router = APIRouter(tags=["EmailTest"])


@router.get("/test-email")
def test_email(to: str = None):
    """
    Test SMTP by sending a small email.
    Usage: /test-email?to=cburks@slworld.com
    """
    if not to:
        raise HTTPException(status_code=400, detail="Pass ?to=email@address.com")

    success, message = send_email(
        to_addresses=to,
        subject="Safety Observations: SMTP test",
        html_body="<p>If you can read this, SMTP is configured correctly.</p>"
                  "<p>Sent from the Safety Observations app.</p>"
    )

    if not success:
        raise HTTPException(status_code=500, detail=message)
    return {"status": "sent", "detail": message}
@router.get("/test-email-debug")
def test_email_debug():
    """Return what SMTP config the app is loading."""
    import os, socket
    host = os.getenv("SMTP_HOST", "")
    port = os.getenv("SMTP_PORT", "")
    user = os.getenv("SMTP_USER", "")
    has_pwd = bool(os.getenv("SMTP_PASSWORD"))
    
    # Try DNS resolution
    dns_result = None
    try:
        dns_result = socket.gethostbyname(host) if host else "no host set"
    except Exception as e:
        dns_result = f"DNS error: {e}"
    
    return {
        "SMTP_HOST": host,
        "SMTP_PORT": port,
        "SMTP_USER": user,
        "SMTP_PASSWORD_set": has_pwd,
        "host_resolves_to": dns_result
    }