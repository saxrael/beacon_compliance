"""Beacon Compliance OS — Production Direct SMTP Email Service.

Uses Python standard library `smtplib` over Port 587 (STARTTLS) or Port 465 (SSL)
to deliver trustee notifications via direct authenticated SMTP without third-party API locks.
"""

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any


def send_email(
    to_email: str,
    subject: str,
    body_html: str,
    body_text: str | None = None,
) -> dict[str, Any]:
    """Send an email notification via direct authenticated SMTP."""
    from_email = os.environ.get("NOTIFICATION_FROM_EMAIL", "compliance@pottershouse.org.uk")

    smtp_host = os.environ.get("SMTP_HOST")
    if not smtp_host:
        return {
            "success": False,
            "error": "No SMTP_HOST configured in environment.",
        }

    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_user = os.environ.get("SMTP_USERNAME", "")
    smtp_pass = os.environ.get("SMTP_PASSWORD", "")
    use_tls = os.environ.get("SMTP_USE_TLS", "true").lower() in ("true", "1")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = from_email
    msg["To"] = to_email

    if body_text:
        msg.attach(MIMEText(body_text, "plain"))
    msg.attach(MIMEText(body_html, "html"))

    try:
        if smtp_port == 465:
            with smtplib.SMTP_SSL(smtp_host, smtp_port) as server:
                if smtp_user and smtp_pass:
                    server.login(smtp_user, smtp_pass)
                server.sendmail(from_email, [to_email], msg.as_string())
        else:
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                if use_tls:
                    server.starttls()
                if smtp_user and smtp_pass:
                    server.login(smtp_user, smtp_pass)
                server.sendmail(from_email, [to_email], msg.as_string())

        return {
            "success": True,
            "provider": "smtp",
            "message": f"Email sent to {to_email } via SMTP",
        }
    except Exception as e:
        return {"success": False, "provider": "smtp", "error": str(e)}
