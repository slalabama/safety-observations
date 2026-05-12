import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.office365.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
EMAIL_FROM = os.getenv("EMAIL_FROM", SMTP_USER)


def send_email(to_addresses, subject, html_body, attachments=None):
    """
    Send an email via SMTP.

    to_addresses: list of recipient emails (or single string)
    subject: email subject
    html_body: HTML content
    attachments: list of dicts [{"filename": "x.pdf", "data": bytes, "mime": "application/pdf"}]

    Returns (success: bool, message: str)
    """
    if isinstance(to_addresses, str):
        to_addresses = [to_addresses]

    if not SMTP_USER or not SMTP_PASSWORD:
        return False, "SMTP credentials not configured"

    if not to_addresses:
        return False, "No recipients"

    msg = MIMEMultipart()
    msg["From"] = EMAIL_FROM
    msg["To"] = ", ".join(to_addresses)
    msg["Subject"] = subject

    msg.attach(MIMEText(html_body, "html"))

    if attachments:
        for att in attachments:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(att["data"])
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f'attachment; filename="{att["filename"]}"'
            )
            msg.attach(part)

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=20) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(EMAIL_FROM, to_addresses, msg.as_string())
        return True, f"Sent to {len(to_addresses)} recipient(s)"
    except Exception as e:
        return False, f"{type(e).__name__}: {str(e)}"