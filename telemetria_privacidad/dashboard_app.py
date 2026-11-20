"""
Dashboard de Telemetría Pedagógica y Auditoría de Privacidad.
Escucha por defecto en http://127.0.0.1:8003.
"""

from __future__ import annotations

import logging
from pathlib import Path

from flask import Flask, jsonify, render_template

from config.settings import (
    BIND_HOST,
    CAMPAIGN_ID,
    DASHBOARD_PORT,
    ORG_NAME,
    PORTAL_EVIL_TWIN_URL,
    PORTAL_LEGITIMO_URL,
    RETENTION_DAYS,
    WEBMAIL_URL,
)
from telemetria_privacidad.sanitizer import EVENT_JUSTIFICATIONS
from telemetria_privacidad.storage import TelemetryStore

logging.getLogger("werkzeug").setLevel(logging.WARNING)


def create_dashboard_app(store: TelemetryStore | None = None) -> Flask:
    app = Flask(
        __name__,
        template_folder=str(Path(__file__).resolve().parent / "templates"),
    )
    telemetry = store or TelemetryStore()

    @app.route("/")
    def index():
        metrics = telemetry.get_aggregated_metrics()
        events = telemetry.list_events(limit=150)
        return render_template(
            "dashboard.html",
            org_name=ORG_NAME,
            campaign_id=CAMPAIGN_ID,
            retention_days=RETENTION_DAYS,
            metrics=metrics,
            events=events,
            justifications=EVENT_JUSTIFICATIONS,
            webmail_url=WEBMAIL_URL,
            portal_legitimo_url=PORTAL_LEGITIMO_URL,
            portal_evil_twin_url=PORTAL_EVIL_TWIN_URL,
        )

    @app.route("/api/metrics")
    def api_metrics():
        return jsonify(telemetry.get_aggregated_metrics())

    @app.route("/api/events")
    def api_events():
        return jsonify(telemetry.list_events(limit=200))

    @app.route("/health")
    def health():
        return jsonify({"status": "ok", "service": "dashboard_telemetria"})

    return app


def main() -> None:
    app = create_dashboard_app()
    print(f"[Dashboard Telemetría] Disponible en http://{BIND_HOST}:{DASHBOARD_PORT}")
    app.run(host=BIND_HOST, port=DASHBOARD_PORT, debug=False, use_reloader=False)


if __name__ == "__main__":
    main()
