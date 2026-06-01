"""
Email Service — compose & send emails using organization data.

Supports:
    - Template-based emails with {{placeholder}} substitution
    - Bulk email to filtered record subsets
    - SMTP sending (configurable per deployment)
    - Full audit logging in email_logs table
"""

import os
import re
import smtplib
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

import models

# ──────────── SMTP Config (from environment) ─────────────────


def _get_smtp_config() -> Dict[str, Any]:
    return {
        "host": os.getenv("SMTP_HOST", "smtp.gmail.com"),
        "port": int(os.getenv("SMTP_PORT", "587")),
        "user": os.getenv("SMTP_USER", ""),
        "password": os.getenv("SMTP_PASSWORD", ""),
        "from_email": os.getenv("SMTP_FROM_EMAIL", ""),
        "from_name": os.getenv("SMTP_FROM_NAME", "NexusAI"),
        "use_tls": os.getenv("SMTP_USE_TLS", "true").lower() == "true",
    }


# ──────────── Template Rendering ─────────────────────────────


def render_template(
    template: str,
    data: Dict[str, Any],
) -> str:
    """Replace {{field_key}} placeholders with actual values from a data row."""

    def replacer(match: re.Match) -> str:
        key = match.group(1).strip()
        val = data.get(key)
        return str(val) if val is not None else ""

    return re.sub(r"\{\{(.+?)\}\}", replacer, template)


def extract_placeholders(template: str) -> List[str]:
    """Extract all {{placeholder}} keys from a template."""
    return list(set(re.findall(r"\{\{(.+?)\}\}", template)))


# ──────────── Email Template CRUD ────────────────────────────


def create_template(
    org_id: int,
    name: str,
    subject: str,
    body_html: str,
    db: Session,
) -> models.EmailTemplate:
    placeholders = extract_placeholders(body_html + " " + subject)
    template = models.EmailTemplate(
        org_id=org_id,
        name=name,
        subject=subject,
        body_html=body_html,
        placeholders=placeholders,
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    return template


def get_templates(org_id: int, db: Session) -> List[models.EmailTemplate]:
    return db.query(models.EmailTemplate).filter(
        models.EmailTemplate.org_id == org_id,
    ).order_by(models.EmailTemplate.created_at.desc()).all()


def get_template(template_id: int, org_id: int, db: Session) -> Optional[models.EmailTemplate]:
    return db.query(models.EmailTemplate).filter(
        models.EmailTemplate.id == template_id,
        models.EmailTemplate.org_id == org_id,
    ).first()


def delete_template(template_id: int, org_id: int, db: Session) -> bool:
    template = get_template(template_id, org_id, db)
    if not template:
        return False
    db.delete(template)
    db.commit()
    return True


# ──────────── Send Emails ────────────────────────────────────


def _send_single_email(
    to_email: str,
    to_name: Optional[str],
    subject: str,
    body_html: str,
    smtp_config: Dict[str, Any],
) -> Optional[str]:
    """Send one email via SMTP. Returns error message on failure, None on success."""
    if not smtp_config["user"] or not smtp_config["password"]:
        return "SMTP not configured (missing SMTP_USER / SMTP_PASSWORD)"

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{smtp_config['from_name']} <{smtp_config['from_email'] or smtp_config['user']}>"
        msg["To"] = f"{to_name} <{to_email}>" if to_name else to_email
        msg.attach(MIMEText(body_html, "html"))

        with smtplib.SMTP(smtp_config["host"], smtp_config["port"]) as server:
            if smtp_config["use_tls"]:
                server.starttls()
            server.login(smtp_config["user"], smtp_config["password"])
            server.send_message(msg)
        return None
    except Exception as exc:
        return str(exc)


def send_bulk_email(
    org_id: int,
    user_id: int,
    source_id: int,
    rows: List[Dict[str, Any]],
    email_field: str,
    name_field: Optional[str],
    subject_template: str,
    body_template: str,
    db: Session,
    template_id: Optional[int] = None,
) -> Dict[str, Any]:
    """Send templated emails to a list of data rows."""
    smtp_config = _get_smtp_config()
    results = []
    queued = 0
    failed = 0

    for row in rows:
        recipient_email = row.get(email_field)
        if not recipient_email or not isinstance(recipient_email, str) or "@" not in recipient_email:
            failed += 1
            results.append({"row": row.get("id", "?"), "status": "skipped", "reason": "invalid email"})
            continue

        recipient_name = row.get(name_field) if name_field else None
        rendered_subject = render_template(subject_template, row)
        rendered_body = render_template(body_template, row)

        error = _send_single_email(
            recipient_email, recipient_name, rendered_subject, rendered_body, smtp_config,
        )

        now = datetime.now(timezone.utc)
        log = models.EmailLog(
            org_id=org_id,
            user_id=user_id,
            source_id=source_id,
            template_id=template_id,
            recipient_email=recipient_email,
            recipient_name=str(recipient_name) if recipient_name else None,
            subject=rendered_subject,
            body_html=rendered_body,
            status="sent" if error is None else "failed",
            sent_at=now if error is None else None,
            error_message=error,
        )
        db.add(log)

        if error:
            failed += 1
            results.append({"email": recipient_email, "status": "failed", "error": error})
        else:
            queued += 1
            results.append({"email": recipient_email, "status": "sent"})

    db.commit()
    return {
        "total_recipients": len(rows),
        "queued": queued,
        "failed": failed,
        "details": results,
    }


def get_email_logs(
    org_id: int, db: Session, limit: int = 50, offset: int = 0,
) -> List[models.EmailLog]:
    return db.query(models.EmailLog).filter(
        models.EmailLog.org_id == org_id,
    ).order_by(models.EmailLog.created_at.desc()).offset(offset).limit(limit).all()
