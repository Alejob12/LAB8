"""
Interfaz Webmail corporativa simulada + Inspector de Cola de Correos y Logs SMTP.
Escucha por defecto en http://127.0.0.1:8025.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from flask import Flask, jsonify, render_template, request
from markupsafe import escape

from config.settings import (
    BIND_HOST,
    DASHBOARD_URL,
    ORG_DOMAIN,
    ORG_NAME,
    PORTAL_EVIL_TWIN_URL,
    PORTAL_LEGITIMO_URL,
    USUARIOS_FICTICIOS_PATH,
    WEBMAIL_PORT,
)
from servidor_correo.mail_storage import MailStorage

logging.getLogger("werkzeug").setLevel(logging.WARNING)


def create_webmail_app(storage: MailStorage | None = None) -> Flask:
    app = Flask(
        __name__,
        template_folder=str(Path(__file__).resolve().parent / "templates"),
    )
    mail_storage = storage or MailStorage()

    def load_users() -> list[dict]:
        if USUARIOS_FICTICIOS_PATH.exists():
            return json.loads(USUARIOS_FICTICIOS_PATH.read_text(encoding="utf-8"))
        return []

    @app.route("/")
    def index():
        tab = request.args.get("tab", "inbox")
        selected_user = request.args.get("user", "").strip()
        selected_msg_id = request.args.get("msg", "").strip()

        users = load_users()
        messages = mail_storage.list_messages(recipient=selected_user or None)
        queue_items = mail_storage.list_queue()
        smtp_logs = mail_storage.read_smtp_logs(max_lines=150)

        active_msg = None
        if selected_msg_id:
            active_msg = mail_storage.get_message(selected_msg_id)
        elif messages:
            active_msg = messages[0]

        return render_template(
            "webmail.html",
            org_name=ORG_NAME,
            org_domain=ORG_DOMAIN,
            tab=tab,
            users=users,
            selected_user=selected_user,
            messages=messages,
            active_msg=active_msg,
            queue_items=queue_items,
            smtp_logs=smtp_logs,
            portal_legitimo_url=PORTAL_LEGITIMO_URL,
            portal_evil_twin_url=PORTAL_EVIL_TWIN_URL,
            dashboard_url=DASHBOARD_URL,
        )

    @app.route("/message/<path:message_id>/html")
    def message_html(message_id: str):
        msg = mail_storage.get_message(message_id)
        if not msg:
            return "Mensaje no encontrado", 404
        return msg.get("html_body") or f"<pre>{escape(msg.get('text_body', ''))}</pre>"

    @app.route("/api/messages")
    def api_messages():
        recipient = request.args.get("recipient")
        return jsonify(mail_storage.list_messages(recipient=recipient))

    @app.route("/api/queue")
    def api_queue():
        return jsonify(mail_storage.list_queue())

    @app.route("/api/smtp-logs")
    def api_smtp_logs():
        return jsonify({"lines": mail_storage.read_smtp_logs(max_lines=200)})

    @app.route("/health")
    def health():
        return jsonify({"status": "ok", "service": "webmail_simulado"})

    return app


def main() -> None:
    app = create_webmail_app()
    print(f"[Webmail Simulado] Disponible en http://{BIND_HOST}:{WEBMAIL_PORT}")
    app.run(host=BIND_HOST, port=WEBMAIL_PORT, debug=False, use_reloader=False)


if __name__ == "__main__":
    main()
