"""
Pruebas de Restricción de Alcance y Allowlist SMTP — AndesCorp S.A.
Garantiza que el servidor de correo simulado NUNCA envíe correos fuera de @andescorp.local.
"""

import asyncio
import smtplib
from email.message import EmailMessage

import pytest

from config.settings import BIND_HOST, ORG_DOMAIN, is_allowed_recipient
from servidor_correo.mail_storage import MailStorage
from servidor_correo.smtp_local import LocalSMTPServer


def test_is_allowed_recipient():
    assert is_allowed_recipient("ana.gomez@andescorp.local") is True
    assert is_allowed_recipient("Carlos.Ruiz@AndesCorp.Local") is True
    assert is_allowed_recipient("Mesa de Ayuda <soporte@andescorp.local>") is True
    # Dominios externos o inválidos deben ser estrictamente rechazados
    assert is_allowed_recipient("victima@gmail.com") is False
    assert is_allowed_recipient("empleado@andescorp.com") is False
    assert is_allowed_recipient("atacante@andescorp-ti.local") is False
    assert is_allowed_recipient("invalido") is False
    assert is_allowed_recipient("") is False


@pytest.mark.asyncio
async def test_smtp_server_rejects_external_recipients(tmp_path):
    db_path = tmp_path / "mail_test.db"
    log_path = tmp_path / "smtp_test.log"
    queue_log = tmp_path / "queue_test.jsonl"
    storage = MailStorage(db_path=db_path, smtp_log_path=log_path, queue_log_path=queue_log)

    test_port = 11025
    server = LocalSMTPServer(host=BIND_HOST, port=test_port, storage=storage)
    await server.start()

    def run_smtp_client_tests():
        # 1. Intento de envío a dominio externo -> debe fallar con 550
        with pytest.raises(smtplib.SMTPRecipientsRefused) as exc_info:
            with smtplib.SMTP(BIND_HOST, test_port, timeout=5) as client:
                client.ehlo("tester.local")
                msg = EmailMessage()
                msg["From"] = f"soporte@{ORG_DOMAIN}"
                msg["To"] = "empleado_real@gmail.com"
                msg["Subject"] = "Prueba Externa Prohibida"
                msg.set_content("Contenido")
                client.send_message(msg)

        refused = exc_info.value.recipients
        assert "empleado_real@gmail.com" in refused
        code, _ = refused["empleado_real@gmail.com"]
        assert code == 550

        # 2. Envío a destinatario de la organización ficticia -> debe ser aceptado
        with smtplib.SMTP(BIND_HOST, test_port, timeout=5) as client:
            client.ehlo("tester.local")
            msg_ok = EmailMessage()
            msg_ok["From"] = f"soporte@{ORG_DOMAIN}"
            msg_ok["To"] = f"ana.gomez@{ORG_DOMAIN}"
            msg_ok["Subject"] = "Mensaje Legítimo Interno"
            msg_ok.set_content("Prueba interna exitosa")
            client.send_message(msg_ok)

    try:
        await asyncio.to_thread(run_smtp_client_tests)
        messages = storage.list_messages(recipient=f"ana.gomez@{ORG_DOMAIN}")
        assert len(messages) == 1
        assert messages[0]["subject"] == "Mensaje Legítimo Interno"
    finally:
        await server.stop()
