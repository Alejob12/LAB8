"""
Pruebas de Privacidad por Diseño y Cero Retención de Contraseñas (Lab 8).
Verifica que las contraseñas jamás ingresen a bases de datos, logs o respuestas.
"""

import json
import sqlite3

from portal_evil_twin.app import create_evil_twin_app
from telemetria_privacidad.sanitizer import is_sensitive_key, strip_sensitive_fields
from telemetria_privacidad.storage import TelemetryStore


def test_strip_sensitive_fields():
    dirty_payload = {
        "email": "ana.gomez@andescorp.local",
        "password": "SuperSecretPassword123!",
        "confirm_pwd": "SuperSecretPassword123!",
        "token": "tok_123456",
        "mfa_pin": "999888",
        "metadata": {
            "clave": "otra_clave",
            "browser": "Chrome",
        },
    }

    clean, dropped = strip_sensitive_fields(dirty_payload)
    assert dropped is True
    assert "password" not in clean
    assert "confirm_pwd" not in clean
    assert "mfa_pin" not in clean
    assert "clave" not in clean.get("metadata", {})
    assert clean["email"] == "ana.gomez@andescorp.local"
    assert clean["token"] == "tok_123456"
    assert clean["metadata"]["browser"] == "Chrome"


def test_evil_twin_never_stores_passwords(tmp_path):
    db_path = tmp_path / "telemetry_test.db"
    log_path = tmp_path / "interactions_test.jsonl"
    store = TelemetryStore(db_path=db_path, log_path=log_path)

    # Registrar usuario
    reg = store.register_participant("ana.gomez@andescorp.local", "Ana Gómez", "Finanzas")
    token = reg["token"]

    app = create_evil_twin_app(store=store)
    client = app.test_client()

    secret_password = "ULTRA_CONFIDENTIAL_PASSWORD_XYZ_999!"

    # Simular envío del formulario con la contraseña secreta
    response = client.post(
        f"/login?t={token}",
        data={
            "token": token,
            "email": "ana.gomez@andescorp.local",
            "password": secret_password,
        },
        follow_redirects=False,
    )

    # Debe redirigir a la página educativa
    assert response.status_code == 302
    assert "/educacion" in response.headers["Location"]

    # 1. Verificar que el secreto no está en el log JSONL
    log_text = log_path.read_text(encoding="utf-8")
    assert secret_password not in log_text

    # 2. Verificar que el secreto no está en la base de datos SQLite
    conn = sqlite3.connect(db_path)
    events = conn.execute("SELECT * FROM interaction_events WHERE event_type = 'FORM_SUBMITTED'").fetchall()
    assert len(events) == 1
    # Inspeccionar todas las columnas del registro
    for row in events:
        for val in row:
            assert secret_password not in str(val)
    conn.close()

    # 3. Verificar que las banderas de descarte se registraron correctamente
    ev = store.list_events()[0]
    assert ev["event_type"] == "FORM_SUBMITTED"
    assert ev["had_password_input"] == 1
    assert ev["sensitive_fields_dropped"] == 1
    assert ev["participant_pseudonym"] == reg["participant_pseudonym"]
