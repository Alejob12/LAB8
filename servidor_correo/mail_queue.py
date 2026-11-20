"""
Servicio de cola de correos (Mail Queue) y despacho SMTP hacia el servidor Mail local.

Todos los envíos de la simulación y de los correos formativos pasan por esta cola,
dejando evidencia trazable en `mail_server.db` y `logs/mail_queue.jsonl`.
"""

from __future__ import annotations

import smtplib
import uuid
from email.message import EmailMessage
from email.utils import formataddr, formatdate
from typing import Any

from config.settings import (
    CAMPAIGN_ID,
    ORG_DOMAIN,
    SMTP_HOST,
    SMTP_PORT,
    is_allowed_recipient,
)
from servidor_correo.mail_storage import MailStorage


class MailQueueService:
    def __init__(
        self,
        smtp_host: str = SMTP_HOST,
        smtp_port: int = SMTP_PORT,
        storage: MailStorage | None = None,
    ) -> None:
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.storage = storage or MailStorage()

    def enqueue_and_deliver(
        self,
        *,
        category: str,
        sender_name: str,
        sender_email: str,
        recipient_email: str,
        subject: str,
        text_body: str,
        html_body: str,
        campaign_id: str = CAMPAIGN_ID,
    ) -> dict[str, Any]:
        """
        Encola un correo y lo transmite al servidor SMTP local de la organización.
        Bloquea cualquier destinatario fuera de la allowlist antes y durante el envío.
        """
        queue_id = self.storage.enqueue_item(
            category=category,
            sender=sender_email,
            recipient=recipient_email,
            subject=subject,
        )

        # Control preventivo de alcance antes de tocar el socket SMTP
        if not is_allowed_recipient(recipient_email):
            reason = f"550 BLOCKED_BY_ALLOWLIST: solo se permiten correos @{ORG_DOMAIN}"
            self.storage.update_queue_status(
                queue_id,
                status="REJECTED",
                smtp_response=reason,
                increment_attempt=True,
            )
            return {
                "queue_id": queue_id,
                "status": "REJECTED",
                "recipient": recipient_email,
                "smtp_response": reason,
            }

        self.storage.update_queue_status(
            queue_id,
            status="PROCESSING",
            smtp_response="Connecting to local SMTP",
            increment_attempt=True,
        )

        msg = EmailMessage()
        msg["Message-ID"] = f"<{uuid.uuid4().hex}@mail.{ORG_DOMAIN}>"
        msg["Date"] = formatdate(localtime=True)
        msg["From"] = formataddr((sender_name, sender_email))
        msg["To"] = recipient_email
        msg["Subject"] = subject
        msg["X-Lab-Simulation"] = "true"
        msg["X-Campaign-ID"] = campaign_id
        msg["X-Mail-Category"] = category
        msg["X-Queue-ID"] = queue_id
        msg.set_content(text_body, subtype="plain", charset="utf-8")
        msg.add_alternative(html_body, subtype="html", charset="utf-8")

        try:
            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=10) as client:
                client.ehlo(f"dispatcher.{ORG_DOMAIN}")
                refused = client.send_message(msg, from_addr=sender_email, to_addrs=[recipient_email])
                if refused:
                    resp = f"REFUSED: {refused}"
                    self.storage.update_queue_status(queue_id, status="REJECTED", smtp_response=resp)
                    return {
                        "queue_id": queue_id,
                        "status": "REJECTED",
                        "recipient": recipient_email,
                        "smtp_response": resp,
                    }
            self.storage.update_queue_status(
                queue_id,
                status="DELIVERED",
                smtp_response="250 2.0.0 OK delivered to local mailbox",
            )
            return {
                "queue_id": queue_id,
                "status": "DELIVERED",
                "recipient": recipient_email,
                "message_id": msg["Message-ID"],
                "smtp_response": "250 2.0.0 OK delivered to local mailbox",
            }
        except smtplib.SMTPRecipientsRefused as exc:
            resp = str(exc.recipients)
            self.storage.update_queue_status(queue_id, status="REJECTED", smtp_response=resp)
            return {
                "queue_id": queue_id,
                "status": "REJECTED",
                "recipient": recipient_email,
                "smtp_response": resp,
            }
        except Exception as exc:
            resp = f"SMTP_ERROR: {exc}"
            self.storage.update_queue_status(queue_id, status="FAILED", smtp_response=resp)
            return {
                "queue_id": queue_id,
                "status": "FAILED",
                "recipient": recipient_email,
                "smtp_response": resp,
            }
