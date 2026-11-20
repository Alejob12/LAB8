"""
Portal de Inicio de Sesión Corporativo (SSO Legítimo) — AndesCorp S.A.
Escucha por defecto en http://127.0.0.1:8001 (simula https://sso.andescorp.local).

Además de representar el destino legítimo al que siempre se redirige al usuario tras
la página educativa, sirve de forma local los materiales de formación de RR.HH.
"""

from __future__ import annotations

import logging
from pathlib import Path

from flask import Flask, jsonify, render_template, request, send_from_directory

from config.settings import (
    BIND_HOST,
    CSIRT_EMAIL,
    CSIRT_EXTENSION,
    DASHBOARD_URL,
    LEGIT_DISPLAY_HOST,
    MATERIALES_DIR,
    ORG_DOMAIN,
    ORG_NAME,
    PORTAL_LEGITIMO_PORT,
    WEBMAIL_URL,
)

logging.getLogger("werkzeug").setLevel(logging.WARNING)


def create_legit_portal_app() -> Flask:
    app = Flask(
        __name__,
        template_folder=str(Path(__file__).resolve().parent / "templates"),
    )

    @app.route("/", methods=["GET", "POST"])
    @app.route("/login", methods=["GET", "POST"])
    def login():
        from_simulation = request.args.get("from_simulation") == "1"
        session_user = None
        error_msg = None

        if request.method == "POST":
            # Entorno estrictamente de demostración: nunca persiste ni imprime contraseñas
            email_val = (request.form.get("email") or "").strip().lower()
            if email_val.endswith(f"@{ORG_DOMAIN}"):
                session_user = email_val
                return render_template(
                    "panel_sso.html",
                    org_name=ORG_NAME,
                    org_domain=ORG_DOMAIN,
                    display_host=LEGIT_DISPLAY_HOST,
                    user_email=session_user,
                    csirt_email=CSIRT_EMAIL,
                    csirt_extension=CSIRT_EXTENSION,
                    webmail_url=WEBMAIL_URL,
                    dashboard_url=DASHBOARD_URL,
                )
            error_msg = (
                f"Usa un correo ficticio válido del dominio @{ORG_DOMAIN} "
                "(por ejemplo: ana.gomez@andescorp.local)."
            )

        return render_template(
            "login_legitimo.html",
            org_name=ORG_NAME,
            org_domain=ORG_DOMAIN,
            display_host=LEGIT_DISPLAY_HOST,
            from_simulation=from_simulation,
            error_msg=error_msg,
            csirt_email=CSIRT_EMAIL,
            csirt_extension=CSIRT_EXTENSION,
            webmail_url=WEBMAIL_URL,
            dashboard_url=DASHBOARD_URL,
        )

    @app.route("/materiales/<path:filename>")
    def materiales(filename: str):
        """Sirve los materiales de formación de RR.HH. (infografía, checklist, guía)."""
        return send_from_directory(str(MATERIALES_DIR), filename)

    @app.route("/health")
    def health():
        return jsonify({"status": "ok", "service": "portal_sso_legitimo"})

    return app


def main() -> None:
    app = create_legit_portal_app()
    print(f"[Portal SSO Legítimo] Disponible en http://{BIND_HOST}:{PORTAL_LEGITIMO_PORT}")
    app.run(host=BIND_HOST, port=PORTAL_LEGITIMO_PORT, debug=False, use_reloader=False)


if __name__ == "__main__":
    main()
