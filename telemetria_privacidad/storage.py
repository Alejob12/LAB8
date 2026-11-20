"""
Almacenamiento de telemetría mínima y gestión de mapeo efímero de campaña.

Características de privacidad:
- SQLite configurado con `PRAGMA secure_delete = ON` para sobreescribir páginas borradas.
- La tabla `interaction_events` jamás almacena correos en claro ni contraseñas.
- Los logs estructurados `interactions.jsonl` contienen exclusivamente el esquema sanitizado.
"""

from __future__ import annotations

import json
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from config.settings import (
    CAMPAIGN_ID,
    INTERACTIONS_LOG_PATH,
    TELEMETRY_DB_PATH,
)
from telemetria_privacidad.sanitizer import (
    EVENT_JUSTIFICATIONS,
    classify_user_agent,
    generate_tracking_token,
    pseudonymize_email,
    sanitize_path,
    validate_telemetry_record,
)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class TelemetryStore:
    """Gestor de telemetría pedagógica y registro de eventos sanitizados."""

    def __init__(
        self,
        db_path: Path | None = None,
        log_path: Path | None = None,
    ) -> None:
        self.db_path = Path(db_path) if db_path else TELEMETRY_DB_PATH
        self.log_path = Path(log_path) if log_path else INTERACTIONS_LOG_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
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
            # Tabla efímera de campaña (purgada al finalizar con purga_segura.py)
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS campaign_tokens (
                    token TEXT PRIMARY KEY,
                    campaign_id TEXT NOT NULL,
                    participant_pseudonym TEXT NOT NULL,
                    recipient_email TEXT NOT NULL,
                    recipient_name TEXT NOT NULL,
                    department TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    training_sent_at TEXT
                );
                """
            )
            # Tabla de telemetría estrictamente sanitizada (cero contraseñas, cero correos)
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS interaction_events (
                    event_id TEXT PRIMARY KEY,
                    campaign_id TEXT NOT NULL,
                    participant_pseudonym TEXT NOT NULL,
                    department TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    timestamp_utc TEXT NOT NULL,
                    http_method TEXT NOT NULL,
                    path_sanitized TEXT NOT NULL,
                    user_agent_family TEXT NOT NULL,
                    had_password_input INTEGER NOT NULL DEFAULT 0,
                    sensitive_fields_dropped INTEGER NOT NULL DEFAULT 0,
                    pedagogical_justification TEXT NOT NULL
                );
                """
            )

    def register_participant(
        self,
        email: str,
        name: str,
        department: str,
        campaign_id: str = CAMPAIGN_ID,
    ) -> dict[str, str]:
        """Registra un usuario ficticio y devuelve su token opaco y pseudónimo."""
        token = generate_tracking_token(email)
        pseudonym = pseudonymize_email(email)
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO campaign_tokens (
                    token, campaign_id, participant_pseudonym,
                    recipient_email, recipient_name, department, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (token, campaign_id, pseudonym, email.lower().strip(), name, department, utc_now_iso()),
            )
        return {
            "token": token,
            "participant_pseudonym": pseudonym,
            "department": department,
        }

    def resolve_token(self, token: str | None) -> dict[str, Any] | None:
        """Resuelve un token efímero únicamente en memoria para enrutar el correo formativo."""
        if not token:
            return None
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM campaign_tokens WHERE token = ?",
                (token.strip(),),
            ).fetchone()
            return dict(row) if row else None

    def mark_training_sent(self, token: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE campaign_tokens SET training_sent_at = ? WHERE token = ?",
                (utc_now_iso(), token),
            )

    def record_event(
        self,
        event_type: str,
        participant_pseudonym: str = "usr_anonimo",
        department: str = "No especificado",
        http_method: str = "INTERNAL",
        raw_path: str = "/",
        user_agent: str | None = None,
        had_password_input: bool = False,
        sensitive_fields_dropped: bool = False,
        campaign_id: str = CAMPAIGN_ID,
    ) -> dict[str, Any]:
        """Valida y persiste un evento mínimo sanitizado en SQLite y JSONL."""
        record = validate_telemetry_record(
            {
                "event_id": str(uuid.uuid4()),
                "campaign_id": campaign_id,
                "participant_pseudonym": participant_pseudonym,
                "department": department,
                "event_type": event_type,
                "timestamp_utc": utc_now_iso(),
                "http_method": http_method.upper()[:10],
                "path_sanitized": sanitize_path(raw_path),
                "user_agent_family": classify_user_agent(user_agent),
                "had_password_input": int(bool(had_password_input)),
                "sensitive_fields_dropped": int(bool(sensitive_fields_dropped)),
                "pedagogical_justification": EVENT_JUSTIFICATIONS.get(event_type, ""),
            }
        )

        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO interaction_events (
                    event_id, campaign_id, participant_pseudonym, department,
                    event_type, timestamp_utc, http_method, path_sanitized,
                    user_agent_family, had_password_input, sensitive_fields_dropped,
                    pedagogical_justification
                ) VALUES (
                    :event_id, :campaign_id, :participant_pseudonym, :department,
                    :event_type, :timestamp_utc, :http_method, :path_sanitized,
                    :user_agent_family, :had_password_input, :sensitive_fields_dropped,
                    :pedagogical_justification
                )
                """,
                record,
            )

        with self.log_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")

        return record

    def list_events(self, limit: int = 200) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM interaction_events ORDER BY timestamp_utc DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return [dict(r) for r in rows]

    def get_aggregated_metrics(self) -> dict[str, Any]:
        """Calcula métricas agregadas anónimas para el dashboard y reportes."""
        with self._connect() as conn:
            total_participants = conn.execute(
                "SELECT COUNT(*) AS c FROM campaign_tokens"
            ).fetchone()["c"]

            counts_by_event: dict[str, dict[str, int]] = {}
            for ev in EVENT_JUSTIFICATIONS:
                row = conn.execute(
                    """
                    SELECT
                        COUNT(*) AS total,
                        COUNT(DISTINCT participant_pseudonym) AS unique_users
                    FROM interaction_events
                    WHERE event_type = ?
                    """,
                    (ev,),
                ).fetchone()
                counts_by_event[ev] = {
                    "total": row["total"],
                    "unique_users": row["unique_users"],
                }

            dept_rows = conn.execute(
                """
                SELECT
                    department,
                    COUNT(DISTINCT CASE WHEN event_type = 'EMAIL_SENT' THEN participant_pseudonym END) AS emails_sent,
                    COUNT(DISTINCT CASE WHEN event_type = 'LINK_CLICKED' THEN participant_pseudonym END) AS clicked,
                    COUNT(DISTINCT CASE WHEN event_type = 'FORM_SUBMITTED' THEN participant_pseudonym END) AS submitted,
                    COUNT(DISTINCT CASE WHEN event_type = 'EDUCATIONAL_VIEWED' THEN participant_pseudonym END) AS educated,
                    COUNT(DISTINCT CASE WHEN event_type = 'REDIRECTED_TO_LEGIT' THEN participant_pseudonym END) AS redirected
                FROM interaction_events
                GROUP BY department
                ORDER BY department ASC
                """
            ).fetchall()

            dropped_sensitive_total = conn.execute(
                "SELECT COALESCE(SUM(sensitive_fields_dropped), 0) AS s FROM interaction_events"
            ).fetchone()["s"]

        sent_unique = counts_by_event["EMAIL_SENT"]["unique_users"]
        clicked_unique = counts_by_event["LINK_CLICKED"]["unique_users"]
        submitted_unique = counts_by_event["FORM_SUBMITTED"]["unique_users"]
        educated_unique = counts_by_event["EDUCATIONAL_VIEWED"]["unique_users"]
        redirected_unique = counts_by_event["REDIRECTED_TO_LEGIT"]["unique_users"]
        training_sent_unique = counts_by_event["TRAINING_EMAIL_SENT"]["unique_users"]

        def pct(part: int, whole: int) -> float:
            return round((part / whole) * 100.0, 1) if whole > 0 else 0.0

        return {
            "campaign_id": CAMPAIGN_ID,
            "generated_at_utc": utc_now_iso(),
            "privacy_guarantees": {
                "passwords_stored": 0,
                "cleartext_credentials_logged": False,
                "sensitive_fields_dropped_count": dropped_sensitive_total,
                "pseudonymization": "HMAC-SHA256 (clave efímera por campaña)",
                "sqlite_secure_delete": True,
            },
            "summary": {
                "participants_registered": total_participants,
                "emails_sent_unique": sent_unique,
                "links_clicked_unique": clicked_unique,
                "forms_submitted_unique": submitted_unique,
                "educational_page_viewed_unique": educated_unique,
                "redirected_to_legit_unique": redirected_unique,
                "training_emails_sent_unique": training_sent_unique,
                "click_rate_pct": pct(clicked_unique, sent_unique),
                "submission_rate_pct": pct(submitted_unique, sent_unique),
                "education_completion_pct": pct(educated_unique, submitted_unique),
                "redirection_completion_pct": pct(redirected_unique, educated_unique),
            },
            "events_breakdown": counts_by_event,
            "by_department": [dict(r) for r in dept_rows],
        }
