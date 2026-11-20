"""
Despachador de Campaña de Simulación y Envíos Formativos — AndesCorp S.A.

Se encarga de:
1. Registrar a los participantes ficticios y emitir tokens opacos por campaña.
2. Construir y encolar correos de simulación en el servidor Mail local con trazabilidad completa.
3. Despachar el correo formativo de RR.HH. inmediatamente cuando un participante interactúa.
4. Registrar eventos sanitizados de telemetría sin retener credenciales.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from config.settings import (
    CAMPAIGN_ID,
    CSIRT_EMAIL,
    CSIRT_EXTENSION,
    MATERIALES_DIR,
    ORG_DOMAIN,
    ORG_NAME,
    PLANTILLAS_DIR,
    PORTAL_EVIL_TWIN_URL,
    PORTAL_LEGITIMO_URL,
    SIM_SENDER_EMAIL,
    SIM_SENDER_NAME,
    TRAINING_SENDER_EMAIL,
    TRAINING_SENDER_NAME,
    USUARIOS_FICTICIOS_PATH,
)
from servidor_correo.mail_queue import MailQueueService
from telemetria_privacidad.storage import TelemetryStore


def cargar_usuarios_ficticios(path: Path | None = None) -> list[dict[str, Any]]:
    p = Path(path) if path else USUARIOS_FICTICIOS_PATH
    if not p.exists():
        raise FileNotFoundError(f"No se encontró el archivo de usuarios ficticios en: {p}")
    return json.loads(p.read_text(encoding="utf-8"))


def _render_template(template_str: str, context: dict[str, Any]) -> str:
    rendered = template_str
    for k, v in context.items():
        placeholder = "{{" + k + "}}"
        rendered = rendered.replace(placeholder, str(v))
    return rendered


def preparar_y_enviar_campana(
    telemetry: TelemetryStore | None = None,
    mail_queue: MailQueueService | None = None,
    usuarios: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """
    Ejecuta el despacho de la campaña de simulación para todos los usuarios ficticios.
    """
    store = telemetry or TelemetryStore()
    queue = mail_queue or MailQueueService()
    users = usuarios or cargar_usuarios_ficticios()

    html_template_path = PLANTILLAS_DIR / "correo_simulado.html"
    txt_template_path = PLANTILLAS_DIR / "correo_simulado.txt"

    html_raw = html_template_path.read_text(encoding="utf-8")
    txt_raw = txt_template_path.read_text(encoding="utf-8")

    results: list[dict[str, Any]] = []

    for user in users:
        email = user["email"].strip().lower()
        name = user["nombre"]
        department = user.get("departamento", "General")

        # 1. Registrar participante y obtener token efímero opaco
        reg = store.register_participant(
            email=email,
            name=name,
            department=department,
            campaign_id=CAMPAIGN_ID,
        )
        token = reg["token"]
        pseudonym = reg["participant_pseudonym"]

        # 2. Construir URL al portal evil-twin (puerto 8002)
        evil_twin_url = f"{PORTAL_EVIL_TWIN_URL}/login?t={token}"

        ctx = {
            "NOMBRE_USUARIO": name,
            "DEPARTAMENTO": department,
            "ORG_NAME": ORG_NAME,
            "ORG_DOMAIN": ORG_DOMAIN,
            "CORREO_DESTINO": email,
            "EVIL_TWIN_LINK": evil_twin_url,
            "TOKEN": token,
        }

        subject = f"[URGENTE] Actualización del Certificado de Seguridad SSO — {ORG_NAME}"
        html_body = _render_template(html_raw, ctx)
        text_body = _render_template(txt_raw, ctx)

        # 3. Registrar encolado en telemetría
        store.record_event(
            event_type="EMAIL_QUEUED",
            participant_pseudonym=pseudonym,
            department=department,
            http_method="QUEUE",
            raw_path=f"/mail-queue?category=SIMULATION&token={token[:6]}",
            campaign_id=CAMPAIGN_ID,
        )

        # 4. Despachar al servidor SMTP local de la organización
        deliver_res = queue.enqueue_and_deliver(
            category="SIMULATION",
            sender_name=SIM_SENDER_NAME,
            sender_email=SIM_SENDER_EMAIL,
            recipient_email=email,
            subject=subject,
            text_body=text_body,
            html_body=html_body,
            campaign_id=CAMPAIGN_ID,
        )

        # 5. Si fue entregado al buzón local, registrar EMAIL_SENT
        if deliver_res.get("status") == "DELIVERED":
            store.record_event(
                event_type="EMAIL_SENT",
                participant_pseudonym=pseudonym,
                department=department,
                http_method="SMTP",
                raw_path=f"/smtp/deliver?msg_id={deliver_res.get('message_id', 'sim')}",
                campaign_id=CAMPAIGN_ID,
            )

        results.append({
            "user": email,
            "name": name,
            "token": token,
            "pseudonym": pseudonym,
            "status": deliver_res.get("status"),
            "queue_id": deliver_res.get("queue_id"),
        })

    return {
        "campaign_id": CAMPAIGN_ID,
        "total_dispatched": len(results),
        "results": results,
    }


def enviar_correo_formacion_a_usuario(
    token: str,
    telemetry: TelemetryStore | None = None,
    mail_queue: MailQueueService | None = None,
    force_resend: bool = False,
) -> dict[str, Any] | None:
    """
    Despacha el correo de seguimiento de RR.HH. a quien haya interactuado con la simulación.
    Garantiza no reenviar duplicados salvo force_resend=True.
    """
    store = telemetry or TelemetryStore()
    queue = mail_queue or MailQueueService()

    participant = store.resolve_token(token)
    if not participant:
        return None

    if participant.get("training_sent_at") and not force_resend:
        return {
            "status": "ALREADY_SENT",
            "token": token,
            "recipient": participant["recipient_email"],
            "training_sent_at": participant["training_sent_at"],
        }

    html_template_path = MATERIALES_DIR / "correo-seguimiento-rrhh.html"
    txt_template_path = MATERIALES_DIR / "correo-seguimiento-rrhh.txt"

    html_raw = html_template_path.read_text(encoding="utf-8")
    txt_raw = txt_template_path.read_text(encoding="utf-8")

    ctx = {
        "NOMBRE_USUARIO": participant["recipient_name"],
        "ORG_NAME": ORG_NAME,
        "ORG_DOMAIN": ORG_DOMAIN,
        "CAMPAIGN_ID": CAMPAIGN_ID,
        "CSIRT_EMAIL": CSIRT_EMAIL,
        "CSIRT_EXTENSION": CSIRT_EXTENSION,
        "INFOGRAFIA_URL": f"{PORTAL_LEGITIMO_URL}/materiales/infografia-antiphishing.html",
        "PORTAL_LEGITIMO_URL": f"{PORTAL_LEGITIMO_URL}/login",
    }

    subject = f"[Formación] Gracias por participar en el ejercicio de concientización anti-phishing — {ORG_NAME}"
    html_body = _render_template(html_raw, ctx)
    text_body = _render_template(txt_raw, ctx)

    pseudonym = participant["participant_pseudonym"]
    department = participant["department"]
    recipient_email = participant["recipient_email"]

    # 1. Registrar evento de telemetría TRAINING_EMAIL_QUEUED
    store.record_event(
        event_type="TRAINING_EMAIL_QUEUED",
        participant_pseudonym=pseudonym,
        department=department,
        http_method="QUEUE",
        raw_path=f"/mail-queue?category=TRAINING&token={token[:6]}",
        campaign_id=CAMPAIGN_ID,
    )

    # 2. Despachar a la cola y servidor SMTP local
    deliver_res = queue.enqueue_and_deliver(
        category="TRAINING",
        sender_name=TRAINING_SENDER_NAME,
        sender_email=TRAINING_SENDER_EMAIL,
        recipient_email=recipient_email,
        subject=subject,
        text_body=text_body,
        html_body=html_body,
        campaign_id=CAMPAIGN_ID,
    )

    # 3. Marcar en la tabla efímera de tokens que el correo formativo fue enviado
    if deliver_res.get("status") == "DELIVERED":
        store.mark_training_sent(token)
        store.record_event(
            event_type="TRAINING_EMAIL_SENT",
            participant_pseudonym=pseudonym,
            department=department,
            http_method="SMTP",
            raw_path=f"/smtp/deliver?msg_id={deliver_res.get('message_id', 'training')}",
            campaign_id=CAMPAIGN_ID,
        )

    return {
        "status": deliver_res.get("status"),
        "token": token,
        "recipient": recipient_email,
        "queue_id": deliver_res.get("queue_id"),
        "smtp_response": deliver_res.get("smtp_response"),
    }
