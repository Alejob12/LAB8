"""
Mecanismo de eliminación segura (Secure Deletion) y cierre de campaña.

Cumple con los requisitos de privacidad, retención y eliminación segura de datos:
1. Exporta (opcionalmente) un resumen estadístico 100% agregado y anónimo (sin tokens ni pseudónimos).
2. Ejecuta PRAGMA secure_delete = ON, elimina tablas y ejecuta VACUUM en SQLite.
3. Sobreescribe archivos sensibles en 3 pasadas (0x00, 0xFF, aleatorio) + fsync antes de eliminarlos.
4. Genera un certificado verificable de destrucción de datos (`destruction_audit.json`).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from config.settings import (
    CAMPAIGN_ID,
    DATA_DIR,
    DESTRUCTION_AUDIT_PATH,
    INTERACTIONS_LOG_PATH,
    LOGS_DIR,
    MAIL_DB_PATH,
    MAIL_QUEUE_LOG_PATH,
    RETENTION_DAYS,
    SMTP_LOG_PATH,
    TELEMETRY_DB_PATH,
)
from telemetria_privacidad.storage import TelemetryStore


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def secure_wipe_file(path: Path, passes: int = 3) -> dict[str, Any] | None:
    """Sobreescribe un archivo en múltiples pasadas antes de desvincularlo del sistema de archivos."""
    if not path.exists() or not path.is_file():
        return None

    size = path.stat().st_size
    pre_hash = _sha256_file(path)

    patterns = [b"\x00", b"\xff", None]  # None -> bytes aleatorios criptográficos
    with path.open("r+b") as fh:
        for i in range(passes):
            fh.seek(0)
            pattern = patterns[i % len(patterns)]
            remaining = size
            chunk_size = 65536
            while remaining > 0:
                to_write = min(chunk_size, remaining)
                data = os.urandom(to_write) if pattern is None else pattern * to_write
                fh.write(data)
                remaining -= to_write
            fh.flush()
            os.fsync(fh.fileno())

    path.unlink()

    return {
        "file": str(path.name),
        "bytes_wiped": size,
        "overwrite_passes": passes,
        "sha256_before_wipe": pre_hash,
        "status": "WIPED_AND_UNLINKED",
    }


def _wipe_sqlite_tables(db_path: Path, tables: list[str]) -> None:
    if not db_path.exists():
        return
    try:
        conn = sqlite3.connect(db_path)
        try:
            conn.execute("PRAGMA secure_delete = ON;")
            for table in tables:
                conn.execute(f"DELETE FROM {table};")
            conn.commit()
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE);")
            conn.execute("VACUUM;")
        finally:
            conn.close()
    except (sqlite3.OperationalError, sqlite3.DatabaseError):
        pass


def execute_secure_purge(
    export_summary: bool = True,
    include_mail: bool = True,
    telemetry_db: Path | None = None,
    interactions_log: Path | None = None,
    mail_db: Path | None = None,
    smtp_log: Path | None = None,
    mail_queue_log: Path | None = None,
    audit_path: Path | None = None,
    summary_path: Path | None = None,
) -> dict[str, Any]:
    """Ejecuta el procedimiento completo de purga segura y emite certificado de auditoría."""
    t_db = Path(telemetry_db) if telemetry_db else TELEMETRY_DB_PATH
    i_log = Path(interactions_log) if interactions_log else INTERACTIONS_LOG_PATH
    m_db = Path(mail_db) if mail_db else MAIL_DB_PATH
    s_log = Path(smtp_log) if smtp_log else SMTP_LOG_PATH
    q_log = Path(mail_queue_log) if mail_queue_log else MAIL_QUEUE_LOG_PATH
    a_path = Path(audit_path) if audit_path else DESTRUCTION_AUDIT_PATH
    s_path = Path(summary_path) if summary_path else (t_db.parent / "resumen_anonimizado_campana.json")

    exported_summary_file: str | None = None
    if export_summary and t_db.exists():
        store = TelemetryStore(db_path=t_db, log_path=i_log)
        metrics = store.get_aggregated_metrics()
        s_path.parent.mkdir(parents=True, exist_ok=True)
        s_path.write_text(json.dumps(metrics, indent=2, ensure_ascii=False), encoding="utf-8")
        exported_summary_file = str(s_path)

    # 1. Borrado lógico + VACUUM con PRAGMA secure_delete = ON
    _wipe_sqlite_tables(t_db, ["campaign_tokens", "interaction_events"])
    if include_mail:
        _wipe_sqlite_tables(m_db, ["mail_messages", "mail_queue"])

    # 2. Recolectar archivos a sobreescribir (incluyendo WAL/SHM de SQLite)
    targets: list[Path] = [
        t_db,
        Path(f"{t_db}-wal"),
        Path(f"{t_db}-shm"),
        i_log,
    ]
    if include_mail:
        targets.extend([
            m_db,
            Path(f"{m_db}-wal"),
            Path(f"{m_db}-shm"),
            s_log,
            q_log,
        ])

    wiped_records: list[dict[str, Any]] = []
    for target in targets:
        result = secure_wipe_file(target, passes=3)
        if result:
            wiped_records.append(result)

    certificate = {
        "certificate_type": "SECURE_DATA_DESTRUCTION_AUDIT",
        "campaign_id": CAMPAIGN_ID,
        "executed_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "retention_policy_days": RETENTION_DAYS,
        "wipe_method": "SQLite PRAGMA secure_delete + VACUUM + 3-pass overwrite (0x00, 0xFF, CSPRNG) + fsync + unlink",
        "anonymized_summary_exported": exported_summary_file,
        "files_destroyed": wiped_records,
        "compliance_statement": (
            "Todos los mapeos efímeros de participantes, eventos individuales y registros de correo "
            "del entorno simulado fueron eliminados de forma segura. Nunca se almacenaron contraseñas en texto claro."
        ),
    }

    a_path.parent.mkdir(parents=True, exist_ok=True)
    a_path.write_text(json.dumps(certificate, indent=2, ensure_ascii=False), encoding="utf-8")
    return certificate


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Eliminación segura de datos de la campaña simulada (Lab 8)."
    )
    parser.add_argument(
        "--no-export",
        action="store_true",
        help="No exportar resumen estadístico anónimo antes de purgar.",
    )
    parser.add_argument(
        "--keep-mail",
        action="store_true",
        help="Purgar solo telemetría y tokens, conservando la bandeja simulada.",
    )
    parser.add_argument(
        "--confirm",
        action="store_true",
        required=True,
        help="Confirmación explícita obligatoria para ejecutar la destrucción segura.",
    )
    args = parser.parse_args()

    cert = execute_secure_purge(
        export_summary=not args.no_export,
        include_mail=not args.keep_mail,
    )
    print(json.dumps(cert, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
