"""
Portal Simulado ("Evil-Twin") — AndesCorp S.A.
Escucha por defecto en http://127.0.0.1:8002 (simula http://sso-andescorp-verificacion.local).

Garantías de Privacidad por Diseño (Lab 8):
1. Descarte instantáneo de contraseñas con strip_sensitive_fields() antes de cualquier log o almacenamiento.
2. Cero credenciales retenidas o propagadas.
3. Registro de eventos mínimos de telemetría pedagógica (LINK_CLICKED, FORM_SUBMITTED, EDUCATIONAL_VIEWED, REDIRECTED_TO_LEGIT).
4. Disparo inmediato del correo formativo de RR.HH.
5. Redirección automática y obligatoria al portal legítimo corporativo.
"""

from __future__ import annotations

import logging
from pathlib import Path

from flask import Flask, jsonify, redirect, render_template, request, url_for

from campana_correo.despachador import enviar_correo_formacion_a_usuario
from servidor_correo.mail_queue import MailQueueService
from config.settings import (
    BIND_HOST,
    CSIRT_EMAIL,
    CSIRT_EXTENSION,
    DASHBOARD_URL,
    EVIL_TWIN_DISPLAY_HOST,
    ORG_DOMAIN,
    ORG_NAME,
    PORTAL_EVIL_TWIN_PORT,
    PORTAL_LEGITIMO_URL,
    REDIRECT_COUNTDOWN_SECONDS,
    WEBMAIL_URL,
)
from telemetria_privacidad.sanitizer import (
    pseudonymize_email,
    strip_sensitive_fields,
)
from telemetria_privacidad.storage import TelemetryStore

logging.getLogger("werkzeug").setLevel(logging.WARNING)


def create_evil_twin_app(
    store: TelemetryStore | None = None,
    mail_queue: MailQueueService | None = None,
) -> Flask:
    app = Flask(
        __name__,
        template_folder=str(Path(__file__).resolve().parent / "templates"),
    )
    telemetry = store or TelemetryStore()
    queue = mail_queue or MailQueueService()

    @app.route("/", methods=["GET", "POST"])
    @app.route("/login", methods=["GET", "POST"])
    def login():
        token = (request.args.get("t") or request.form.get("token") or "").strip()
        participant = telemetry.resolve_token(token) if token else None

        if request.method == "POST":
            # 1. Aplicar sanitizador estricto de Privacidad por Diseño
            # Descartar instantáneamente cualquier campo sensible (password, clave, etc.)
            raw_form_dict = request.form.to_dict()
            had_password = bool(
                raw_form_dict.get("password")
                or raw_form_dict.get("passwd")
                or raw_form_dict.get("clave")
            )
            cleaned_payload, dropped_sensitive = strip_sensitive_fields(raw_form_dict)

            email_val = (cleaned_payload.get("email") or "").strip().lower()

            # Determinar pseudónimo y departamento
            if participant:
                pseudonym = participant["participant_pseudonym"]
                department = participant["department"]
            elif email_val:
                pseudonym = pseudonymize_email(email_val)
                department = "General"
            else:
                pseudonym = "usr_anonimo"
                department = "No especificado"

            # 2. Registrar evento mínimo de interacción FORM_SUBMITTED (cero contraseñas)
            telemetry.record_event(
                event_type="FORM_SUBMITTED",
                participant_pseudonym=pseudonym,
                department=department,
                http_method="POST",
                raw_path="/login",
                user_agent=request.headers.get("User-Agent"),
                had_password_input=had_password,
                sensitive_fields_dropped=dropped_sensitive or had_password,
            )

            # 3. Disparar correo formativo de RR.HH. a través del servidor Mail local
            if token:
                try:
                    enviar_correo_formacion_a_usuario(token, telemetry=telemetry, mail_queue=queue)
                except Exception as exc:
                    logging.error(f"[EvilTwin] Error despachando correo formativo: {exc}")

            # 4. Llevar inmediatamente a la página educativa
            target_edu = url_for("educacion")
            if token:
                target_edu += f"?t={token}"
            return redirect(target_edu)

        # GET request
        user_email = ""
        if participant:
            user_email = participant["recipient_email"]
            # Registrar LINK_CLICKED únicamente cuando el usuario entra con su enlace de simulación
            telemetry.record_event(
                event_type="LINK_CLICKED",
                participant_pseudonym=participant["participant_pseudonym"],
                department=participant["department"],
                http_method="GET",
                raw_path="/login",
                user_agent=request.headers.get("User-Agent"),
            )

        return render_template(
            "login_evil_twin.html",
            org_name=ORG_NAME,
            org_domain=ORG_DOMAIN,
            display_host=EVIL_TWIN_DISPLAY_HOST,
            port=PORTAL_EVIL_TWIN_PORT,
            token=token,
            user_email=user_email,
            csirt_email=CSIRT_EMAIL,
            csirt_extension=CSIRT_EXTENSION,
            webmail_url=WEBMAIL_URL,
            dashboard_url=DASHBOARD_URL,
        )

    @app.route("/educacion", methods=["GET"])
    def educacion():
        token = request.args.get("t", "").strip()
        participant = telemetry.resolve_token(token) if token else None

        if participant:
            telemetry.record_event(
                event_type="EDUCATIONAL_VIEWED",
                participant_pseudonym=participant["participant_pseudonym"],
                department=participant["department"],
                http_method="GET",
                raw_path="/educacion",
                user_agent=request.headers.get("User-Agent"),
            )

        redirect_target = url_for("redirigir_legitimo")
        if token:
            redirect_target += f"?t={token}"

        training_sent = bool(participant and participant.get("training_sent_at"))

        return render_template(
            "pagina_educativa.html",
            org_name=ORG_NAME,
            countdown_seconds=REDIRECT_COUNTDOWN_SECONDS,
            redirect_url=redirect_target,
            portal_legitimo_url=PORTAL_LEGITIMO_URL,
            webmail_url=WEBMAIL_URL,
            csirt_email=CSIRT_EMAIL,
            csirt_extension=CSIRT_EXTENSION,
            training_email_sent=training_sent,
        )

    @app.route("/redirigir-legitimo", methods=["GET"])
    def redirigir_legitimo():
        token = request.args.get("t", "").strip()
        participant = telemetry.resolve_token(token) if token else None

        if participant:
            telemetry.record_event(
                event_type="REDIRECTED_TO_LEGIT",
                participant_pseudonym=participant["participant_pseudonym"],
                department=participant["department"],
                http_method="GET",
                raw_path="/redirigir-legitimo",
                user_agent=request.headers.get("User-Agent"),
            )

        dest = f"{PORTAL_LEGITIMO_URL}/login?from_simulation=1"
        return redirect(dest)

    @app.route("/health", methods=["GET"])
    def health():
        return jsonify({"status": "ok", "service": "portal_sso_evil_twin"})

    return app


def main() -> None:
    app = create_evil_twin_app()
    print(f"[Portal Evil-Twin] Disponible en http://{BIND_HOST}:{PORTAL_EVIL_TWIN_PORT}")
    app.run(host=BIND_HOST, port=PORTAL_EVIL_TWIN_PORT, debug=False, use_reloader=False)


if __name__ == "__main__":
    main()
