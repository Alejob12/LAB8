"""
Prueba del Flujo Extremo a Extremo de la Simulación (Lab 8):
1. Envío de campaña a través del servidor Mail local.
2. Clic en el enlace con token (LINK_CLICKED).
3. Envío del formulario de login simulado (FORM_SUBMITTED).
4. Disparo y entrega del correo formativo de RR.HH. (TRAINING_EMAIL_SENT).
5. Visualización de la página educativa (EDUCATIONAL_VIEWED).
6. Redirección final segura al portal legítimo (REDIRECTED_TO_LEGIT).
"""

import asyncio

import pytest

from campana_correo.despachador import preparar_y_enviar_campana
from config.settings import BIND_HOST
from portal_evil_twin.app import create_evil_twin_app
from servidor_correo.mail_queue import MailQueueService
from servidor_correo.mail_storage import MailStorage
from servidor_correo.smtp_local import LocalSMTPServer
from telemetria_privacidad.storage import TelemetryStore


@pytest.mark.asyncio
async def test_full_campaign_flow(tmp_path):
    t_db = tmp_path / "telemetry.db"
    t_log = tmp_path / "interactions.jsonl"
    m_db = tmp_path / "mail.db"
    s_log = tmp_path / "smtp.log"
    q_log = tmp_path / "queue.jsonl"

    store = TelemetryStore(db_path=t_db, log_path=t_log)
    mail_storage = MailStorage(db_path=m_db, smtp_log_path=s_log, queue_log_path=q_log)

    smtp_port = 11026
    smtp_server = LocalSMTPServer(host=BIND_HOST, port=smtp_port, storage=mail_storage)
    await smtp_server.start()

    mail_queue = MailQueueService(
        smtp_host=BIND_HOST,
        smtp_port=smtp_port,
        storage=mail_storage,
    )

    test_user = [{
        "id": "TEST-001",
        "nombre": "Elena Vargas",
        "email": "elena.vargas@andescorp.local",
        "departamento": "Finanzas",
        "cargo": "Auditora",
    }]

    def run_e2e_steps():
        # 1. Despacho de campaña
        res = preparar_y_enviar_campana(
            telemetry=store,
            mail_queue=mail_queue,
            usuarios=test_user,
        )
        assert res["total_dispatched"] == 1
        assert res["results"][0]["status"] == "DELIVERED"
        token = res["results"][0]["token"]

        # Verificar mensaje en el buzón local
        inbox = mail_storage.list_messages(recipient="elena.vargas@andescorp.local")
        assert len(inbox) == 1
        assert "[URGENTE]" in inbox[0]["subject"]

        # 2. Cliente Evil-Twin
        app = create_evil_twin_app(store=store, mail_queue=mail_queue)
        client = app.test_client()

        # Simular GET /login?t=<token> -> LINK_CLICKED
        resp_get = client.get(f"/login?t={token}")
        assert resp_get.status_code == 200
        assert b"sso-andescorp-verificacion.local" in resp_get.data

        # 3. Simular POST /login -> FORM_SUBMITTED + correo formativo
        resp_post = client.post(
            f"/login?t={token}",
            data={
                "token": token,
                "email": "elena.vargas@andescorp.local",
                "password": "PasswordTest123!",
            },
            follow_redirects=False,
        )
        assert resp_post.status_code == 302
        assert "/educacion" in resp_post.headers["Location"]

        # Verificar que el correo formativo fue entregado al buzón de Elena
        inbox_after = mail_storage.list_messages(recipient="elena.vargas@andescorp.local")
        assert len(inbox_after) == 2
        categories = [m["category"] for m in inbox_after]
        assert "SIMULATION" in categories
        assert "TRAINING" in categories

        # 4. Simular GET /educacion?t=<token> -> EDUCATIONAL_VIEWED
        resp_edu = client.get(f"/educacion?t={token}")
        assert resp_edu.status_code == 200
        assert b"Banderas rojas" in resp_edu.data

        # 5. Simular GET /redirigir-legitimo?t=<token> -> REDIRECTED_TO_LEGIT
        resp_redir = client.get(f"/redirigir-legitimo?t={token}", follow_redirects=False)
        assert resp_redir.status_code == 302
        assert "from_simulation=1" in resp_redir.headers["Location"]

        # 6. Validar métricas agregadas en TelemetryStore
        metrics = store.get_aggregated_metrics()
        summary = metrics["summary"]
        assert summary["participants_registered"] == 1
        assert summary["emails_sent_unique"] == 1
        assert summary["links_clicked_unique"] == 1
        assert summary["forms_submitted_unique"] == 1
        assert summary["educational_page_viewed_unique"] == 1
        assert summary["redirected_to_legit_unique"] == 1
        assert summary["training_emails_sent_unique"] == 1
        assert metrics["privacy_guarantees"]["passwords_stored"] == 0

    try:
        await asyncio.to_thread(run_e2e_steps)
    finally:
        await smtp_server.stop()
