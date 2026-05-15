"""
SMTP email helper.

Auto-detects the right TLS mode by port:
    465  -> implicit SMTP over TLS  (smtplib.SMTP_SSL)
    587  -> STARTTLS handshake      (smtplib.SMTP + .starttls())
    25   -> plain                   (smtplib.SMTP)

Reads SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, EMAIL_FROM from
the environment at call time, so changes to Railway variables take effect
on the next request without a redeploy.

Exposes two public functions for backward compatibility with whatever
the routers were calling before:
    send_email(to_addr, subject, body, html=None)  -> (ok: bool, detail: str)
    send_test_email(to_addr=None)                  -> (ok: bool, detail: str)
"""
import os
import smtplib
import ssl
from email.message import EmailMessage
from typing import Optional, Tuple


def _smtp_config():
    host = os.environ.get("SMTP_HOST", "")
    port_raw = os.environ.get("SMTP_PORT", "587")
    user = os.environ.get("SMTP_USER", "")
    pwd = os.environ.get("SMTP_PASSWORD", "")
    sender = os.environ.get("EMAIL_FROM", user or "noreply@example.com")
    try:
        port = int(port_raw)
    except (TypeError, ValueError):
        port = 587
    return host, port, user, pwd, sender


def send_email(
    to_addr: str,
    subject: str,
    body: str,
    html: Optional[str] = None,
) -> Tuple[bool, str]:
    """Send a single email. Returns (ok, detail)."""
    host, port, user, pwd, sender = _smtp_config()

    if not host or not user or not pwd:
        return False, f"SMTP not configured (host={host!r}, user_set={bool(user)}, pwd_set={bool(pwd)})"

    msg = EmailMessage()
    msg["From"] = sender
    msg["To"] = to_addr
    msg["Subject"] = subject
    msg.set_content(body or "")
    if html:
        msg.add_alternative(html, subtype="html")

    try:
        if port == 465:
            # Implicit TLS — encrypted from the first byte
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(host, port, timeout=20, context=context) as s:
                s.login(user, pwd)
                s.send_message(msg)
        else:
            # STARTTLS upgrade on plaintext socket (port 587 / 25)
            with smtplib.SMTP(host, port, timeout=20) as s:
                s.ehlo()
                if port != 25:
                    s.starttls(context=ssl.create_default_context())
                    s.ehlo()
                s.login(user, pwd)
                s.send_message(msg)
        return True, f"sent via {host}:{port} from {sender} to {to_addr}"
    except smtplib.SMTPAuthenticationError as e:
        return False, f"auth failed: {e}"
    except (smtplib.SMTPConnectError, OSError) as e:
        return False, f"connection failed to {host}:{port} — {e}"
    except Exception as e:
        return False, f"send failed: {type(e).__name__}: {e}"


def send_test_email(to_addr: Optional[str] = None) -> Tuple[bool, str]:
    """Convenience wrapper for the /test-email route."""
    _, _, user, _, sender = _smtp_config()
    target = to_addr or sender or user
    return send_email(
        to_addr=target,
        subject="Safety 1st — SMTP test",
        body="If you can read this, outbound mail from Railway is working.",
    )
