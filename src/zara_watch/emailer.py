from __future__ import annotations

import os
import smtplib
from dataclasses import dataclass
from email.message import EmailMessage
from typing import Iterable

from dotenv import load_dotenv


@dataclass(frozen=True)
class EmailSettings:
    smtp_server: str
    smtp_port: int
    username: str
    password: str
    to_emails: list[str]


def load_email_settings() -> EmailSettings | None:
    """
    Loads SMTP settings from env/.env.
    Returns None if not configured (so the app can run without email).
    """
    load_dotenv()

    smtp_server = os.getenv("SMTP_SERVER", "").strip()
    username = os.getenv("EMAIL_USERNAME", "").strip()
    password = os.getenv("EMAIL_PASSWORD", "").strip()
    to_raw = os.getenv("TO_EMAIL", "").strip()
    smtp_port = int(os.getenv("SMTP_PORT", "465"))

    to_emails = [e.strip() for e in to_raw.split(",") if e.strip()]

    if not (smtp_server and username and password and to_emails):
        return None

    return EmailSettings(
        smtp_server=smtp_server,
        smtp_port=smtp_port,
        username=username,
        password=password,
        to_emails=to_emails,
    )


def send_match_email(
    email: EmailSettings,
    *,
    product_url: str,
    product_id: int,
    store_id: int,
    detail: str,
    raw_payload: str,
) -> None:
    subject = f"Zara Alert: AVAILABLE ({detail})"

    body = (
        "Your watched Zara item is now AVAILABLE!\n\n"
        f"Detail: {detail}\n"
        f"Product ID: {product_id}\n"
        f"Store ID: {store_id}\n"
        f"Product URL: {product_url}\n\n"
        "Raw payload:\n"
        f"{raw_payload}\n"
    )

    msg = EmailMessage()
    msg["From"] = email.username
    msg["To"] = ", ".join(email.to_emails)
    msg["Subject"] = subject
    msg.set_content(body)

    with smtplib.SMTP_SSL(email.smtp_server, email.smtp_port) as smtp:
        smtp.login(email.username, email.password)
        smtp.send_message(msg)