"""
Persistencia local para el Servidor Mail simulado de AndesCorp S.A.
Administra:
- Buzones de correo entregados (`mail_messages`)
- Cola de envíos (`mail_queue`) con auditoría en `logs/mail_queue.jsonl`
- Registro SMTP estructurado en `logs/smtp_server.log`
"""

from __future__ import annotations

import email
import json
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from email import policy
from pathlib import Path
from typing import Any, Iterator

from config.settings import MAIL_DB_PATH, MAIL_QUEUE_LOG_PATH, SMTP_LOG_PATH


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class MailStorage:
    def __init__(
        self,
        db_path: Path | None = None,
        smtp_log_path: Path | None = None,
        queue_log_path: Path | None = None,
    ) -> None:
        self.db_path = Path(db_path) if db_path else MAIL_DB_PATH
        self.smtp_log_path = Path(smtp_log_path) if smtp_log_path else SMTP_LOG_PATH
        self.queue_log_path = Path(queue_log_path) if queue_log_path else MAIL_QUEUE_LOG_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.smtp_log_path.parent.mkdir(parents=True, exist_ok=True)
        self.queue_log_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA secure_delete = ON;")
        conn.execute("PRAGMA journal_mode = WAL;")
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS mail_messages (
                    message_id TEXT PRIMARY KEY,
                    queue_id TEXT,
                    category TEXT NOT NULL,
                    mail_from TEXT NOT NULL,
                    rcpt_to TEXT NOT NULL,
                    subject TEXT NOT NULL,
                    text_body TEXT,
                    html_body TEXT,
                    raw_message TEXT NOT NULL,
                    received_at_utc TEXT NOT NULL
                );
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS mail_queue (
                    queue_id TEXT PRIMARY KEY,
                    category TEXT NOT NULL,
                    sender TEXT NOT NULL,
                    recipient TEXT NOT NULL,
                    subject TEXT NOT NULL,
                    status TEXT NOT NULL,
                    attempts INTEGER NOT NULL DEFAULT 0,
                    smtp_response TEXT,
                    enqueued_at_utc TEXT NOT NULL,
                    updated_at_utc TEXT NOT NULL
                );
                """
            )

    def log_smtp(self, level: str, message: str) -> None:
        line = f"[{utc_now_iso()}] [{level.upper()}] {message}\n"
        with self.smtp_log_path.open("a", encoding="utf-8") as fh:
            fh.write(line)

    def _log_queue_transition(self, entry: dict[str, Any]) -> None:
        with self.queue_log_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def enqueue_item(
        self,
        category: str,
        sender: str,
        recipient: str,
        subject: str,
    ) -> str:
        queue_id = f"Q-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6].upper()}"
        now = utc_now_iso()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO mail_queue (
                    queue_id, category, sender, recipient, subject,
                    status, attempts, smtp_response, enqueued_at_utc, updated_at_utc
                ) VALUES (?, ?, ?, ?, ?, 'QUEUED', 0, '', ?, ?)
                """,
                (queue_id, category, sender, recipient, subject, now, now),
            )
        self._log_queue_transition(
            {
                "timestamp_utc": now,
                "queue_id": queue_id,
                "category": category,
                "sender": sender,
                "recipient": recipient,
                "subject": subject,
                "status": "QUEUED",
                "attempts": 0,
            }
        )
        return queue_id

    def update_queue_status(
        self,
        queue_id: str,
        status: str,
        smtp_response: str = "",
        increment_attempt: bool = False,
    ) -> None:
        now = utc_now_iso()
        with self._connect() as conn:
            if increment_attempt:
                conn.execute(
                    """
                    UPDATE mail_queue
                    SET status = ?, smtp_response = ?, attempts = attempts + 1, updated_at_utc = ?
                    WHERE queue_id = ?
                    """,
                    (status, smtp_response, now, queue_id),
                )
            else:
                conn.execute(
                    """
                    UPDATE mail_queue
                    SET status = ?, smtp_response = ?, updated_at_utc = ?
                    WHERE queue_id = ?
                    """,
                    (status, smtp_response, now, queue_id),
                )
            row = conn.execute("SELECT * FROM mail_queue WHERE queue_id = ?", (queue_id,)).fetchone()
        if row:
            self._log_queue_transition(
                {
                    "timestamp_utc": now,
                    "queue_id": queue_id,
                    "category": row["category"],
                    "recipient": row["recipient"],
                    "status": status,
                    "attempts": row["attempts"],
                    "smtp_response": smtp_response,
                }
            )

    def store_received_message(
        self,
        mail_from: str,
        rcpt_to: str,
        raw_bytes: bytes,
    ) -> str:
        parsed = email.message_from_bytes(raw_bytes, policy=policy.default)
        subject = str(parsed.get("Subject", "(Sin asunto)"))
        queue_id = str(parsed.get("X-Queue-ID", ""))
        category = str(parsed.get("X-Mail-Category", "GENERAL"))
        msg_id = str(parsed.get("Message-ID") or f"<{uuid.uuid4().hex}@mail.andescorp.local>")

        text_body = ""
        html_body = ""
        if parsed.is_multipart():
            for part in parsed.walk():
                ctype = part.get_content_type()
                if ctype == "text/plain" and not text_body:
                    text_body = part.get_content()
                elif ctype == "text/html" and not html_body:
                    html_body = part.get_content()
        else:
            if parsed.get_content_type() == "text/html":
                html_body = parsed.get_content()
            else:
                text_body = parsed.get_content()

        received_at = utc_now_iso()
        raw_text = raw_bytes.decode("utf-8", errors="replace")

        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO mail_messages (
                    message_id, queue_id, category, mail_from, rcpt_to,
                    subject, text_body, html_body, raw_message, received_at_utc
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    msg_id,
                    queue_id,
                    category,
                    mail_from,
                    rcpt_to.lower().strip(),
                    subject,
                    text_body,
                    html_body,
                    raw_text,
                    received_at,
                ),
            )
        return msg_id

    def list_messages(self, recipient: str | None = None, limit: int = 200) -> list[dict[str, Any]]:
        with self._connect() as conn:
            if recipient:
                rows = conn.execute(
                    """
                    SELECT * FROM mail_messages
                    WHERE lower(rcpt_to) = lower(?)
                    ORDER BY received_at_utc DESC LIMIT ?
                    """,
                    (recipient.strip(), limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM mail_messages ORDER BY received_at_utc DESC LIMIT ?",
                    (limit,),
                ).fetchall()
            return [dict(r) for r in rows]

    def get_message(self, message_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM mail_messages WHERE message_id = ?",
                (message_id,),
            ).fetchone()
            return dict(row) if row else None

    def list_queue(self, limit: int = 200) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM mail_queue ORDER BY enqueued_at_utc DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return [dict(r) for r in rows]

    def read_smtp_logs(self, max_lines: int = 150) -> list[str]:
        if not self.smtp_log_path.exists():
            return []
        lines = self.smtp_log_path.read_text(encoding="utf-8", errors="replace").splitlines()
        return lines[-max_lines:]
