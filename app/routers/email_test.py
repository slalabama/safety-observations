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