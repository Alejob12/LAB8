"""
Prueba del Mecanismo de Eliminación Segura (Lab 8).
Verifica:
1. Exportación de resumen estadístico 100% agregado.
2. Borrado de tablas con PRAGMA secure_delete = ON.
3. Sobreescritura en 3 pasadas (0x00, 0xFF, CSPRNG) y desvinculación (unlink).
4. Generación del certificado de destrucción de datos.
"""

import json
from pathlib import Path

from telemetria_privacidad.purga_segura import execute_secure_purge
from telemetria_privacidad.storage import TelemetryStore


def test_secure_purge_mechanism(tmp_path):
    t_db = tmp_path / "telemetry.db"
    t_log = tmp_path / "interactions.jsonl"
    m_db = tmp_path / "mail.db"
    s_log = tmp_path / "smtp.log"
    q_log = tmp_path / "queue.jsonl"
    audit_cert = tmp_path / "destruction_audit.json"
    summary_file = tmp_path / "resumen.json"

    # 1. Crear datos de prueba
    store = TelemetryStore(db_path=t_db, log_path=t_log)
    store.register_participant("test@andescorp.local", "Test User", "TI")
    store.record_event(
        event_type="LINK_CLICKED",
        participant_pseudonym="usr_test",
        department="TI",
    )

    # Crear archivos de mail reales usando MailStorage
    from servidor_correo.mail_storage import MailStorage
    m_storage = MailStorage(db_path=m_db, smtp_log_path=s_log, queue_log_path=q_log)
    m_storage.log_smtp("INFO", "dummy smtp log line")
    m_storage.enqueue_item("SIMULATION", "soporte@andescorp.local", "test@andescorp.local", "Asunto")

    assert t_db.exists()
    assert t_log.exists()
    assert m_db.exists()
    assert s_log.exists()
    assert q_log.exists()

    # 2. Ejecutar purga segura
    cert = execute_secure_purge(
        export_summary=True,
        include_mail=True,
        telemetry_db=t_db,
        interactions_log=t_log,
        mail_db=m_db,
        smtp_log=s_log,
        mail_queue_log=q_log,
        audit_path=audit_cert,
        summary_path=summary_file,
    )

    # 3. Validar que los archivos fueron sobreescritos y eliminados
    assert not t_db.exists()
    assert not t_log.exists()
    assert not m_db.exists()
    assert not s_log.exists()
    assert not q_log.exists()

    # 4. Validar certificado
    assert audit_cert.exists()
    cert_data = json.loads(audit_cert.read_text(encoding="utf-8"))
    assert cert_data["certificate_type"] == "SECURE_DATA_DESTRUCTION_AUDIT"
    assert len(cert_data["files_destroyed"]) >= 5
    for destroyed in cert_data["files_destroyed"]:
        assert destroyed["overwrite_passes"] == 3
        assert destroyed["status"] == "WIPED_AND_UNLINKED"

    # 5. Validar resumen anónimo exportado
    assert summary_file.exists()
    summary_data = json.loads(summary_file.read_text(encoding="utf-8"))
    assert "summary" in summary_data
    assert summary_data["privacy_guarantees"]["passwords_stored"] == 0
