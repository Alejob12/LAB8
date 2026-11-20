"""
Sanitizador y controles de Privacidad por Diseño (Privacy by Design).

Garantiza que:
1. Ninguna contraseña o dato sensible pueda ingresar a logs o bases de datos.
2. Los identificadores de usuarios se almacenen únicamente como pseudónimos HMAC-SHA256.
3. Cada tipo de evento registrado tenga una justificación pedagógica explícita.
"""

from __future__ import annotations

import hashlib
import hmac
from typing import Any

from config.settings import CAMPAIGN_HMAC_KEY, FORBIDDEN_SENSITIVE_FIELDS

# Catálogo cerrado de eventos permitidos y su justificación pedagógica
EVENT_JUSTIFICATIONS: dict[str, str] = {
    "EMAIL_QUEUED": (
        "Verificar la preparación y encolado correcto de la campaña en el servidor Mail simulado."
    ),
    "EMAIL_SENT": (
        "Establecer el universo base (denominador) de correos entregados para calcular tasas de concientización."
    ),
    "LINK_CLICKED": (
        "Medir la susceptibilidad inicial ante enlaces con dominios similares (lookalike) en correos de urgencia."
    ),
    "FORM_SUBMITTED": (
        "Identificar cuántos participantes intentaron autenticarse en el portal suplantado (sin guardar credenciales) "
        "para activar la formación inmediata."
    ),
    "TRAINING_EMAIL_QUEUED": (
        "Confirmar el disparo automático del correo de refuerzo formativo en la cola interna de la organización."
    ),
    "TRAINING_EMAIL_SENT": (
        "Garantizar que toda persona que interactuó con el formulario recibió material didáctico de seguimiento."
    ),
    "EDUCATIONAL_VIEWED": (
        "Confirmar que el participante visualizó la página educativa con el análisis de banderas rojas."
    ),
    "REDIRECTED_TO_LEGIT": (
        "Evidenciar el cumplimiento de la condición obligatoria de redirección segura al portal legítimo."
    ),
}

# Esquema cerrado (allowlist) de campos permitidos en registros de telemetría
ALLOWED_TELEMETRY_KEYS = frozenset({
    "event_id",
    "campaign_id",
    "participant_pseudonym",
    "department",
    "event_type",
    "timestamp_utc",
    "http_method",
    "path_sanitized",
    "user_agent_family",
    "had_password_input",
    "sensitive_fields_dropped",
    "pedagogical_justification",
})

_SENSITIVE_SUBSTRINGS = (
    "pass",
    "pwd",
    "clave",
    "contra",
    "secret",
    "cred",
    "otp",
    "mfa",
    "pin",
)


def pseudonymize_email(email_address: str, key: str = CAMPAIGN_HMAC_KEY) -> str:
    """Genera un pseudónimo irreversible sin la clave efímera de campaña."""
    normalized = email_address.strip().lower().encode("utf-8")
    digest = hmac.new(key.encode("utf-8"), b"pseudo|" + normalized, hashlib.sha256).hexdigest()
    return f"usr_{digest[:12]}"


def generate_tracking_token(email_address: str, key: str = CAMPAIGN_HMAC_KEY) -> str:
    """Genera un token opaco por campaña para correlacionar el flujo sin exponer el correo en la URL."""
    normalized = email_address.strip().lower().encode("utf-8")
    digest = hmac.new(key.encode("utf-8"), b"token|" + normalized, hashlib.sha256).hexdigest()
    return digest[:20]


def is_sensitive_key(key_name: str) -> bool:
    """Detecta si un nombre de campo podría contener credenciales o secretos."""
    lowered = key_name.strip().lower()
    if lowered in FORBIDDEN_SENSITIVE_FIELDS:
        return True
    return any(sub in lowered for sub in _SENSITIVE_SUBSTRINGS)


def strip_sensitive_fields(payload: dict[str, Any] | None) -> tuple[dict[str, Any], bool]:
    """
    Elimina inmediatamente cualquier campo sensible de un diccionario (sin leer ni loguear su valor).

    Retorna:
        (diccionario_limpio, hubo_campos_sensibles_descartados)
    """
    if not payload:
        return {}, False

    cleaned: dict[str, Any] = {}
    dropped = False

    for key, value in payload.items():
        if is_sensitive_key(str(key)):
            dropped = True
            # No se lee ni se almacena `value` bajo ninguna circunstancia
            continue
        if isinstance(value, dict):
            sub_clean, sub_dropped = strip_sensitive_fields(value)
            cleaned[key] = sub_clean
            dropped = dropped or sub_dropped
        else:
            cleaned[key] = value

    return cleaned, dropped


def classify_user_agent(user_agent: str | None) -> str:
    """Reduce el User-Agent a una familia general para evitar fingerprinting de dispositivos."""
    if not user_agent:
        return "Desconocido"
    ua = user_agent.lower()
    if "lab8-simulator" in ua or "python-requests" in ua:
        return "Simulador-Lab8"
    if "edg/" in ua or "edge" in ua:
        return "Edge"
    if "firefox/" in ua:
        return "Firefox"
    if "chrome/" in ua and "safari/" in ua:
        return "Chrome"
    if "safari/" in ua:
        return "Safari"
    if "curl/" in ua:
        return "CLI-HTTP"
    return "Otro"


def sanitize_path(raw_path: str | None) -> str:
    """Conserva únicamente la ruta base sin query strings que puedan contener parámetros."""
    if not raw_path:
        return "/"
    return raw_path.split("?", 1)[0][:120]


def validate_telemetry_record(record: dict[str, Any]) -> dict[str, Any]:
    """
    Aplica la allowlist estricta de campos antes de persistir un evento.
    Lanza ValueError si el tipo de evento no está autorizado.
    """
    event_type = record.get("event_type")
    if event_type not in EVENT_JUSTIFICATIONS:
        raise ValueError(f"Tipo de evento no permitido por la política de privacidad: {event_type}")

    sanitized = {k: v for k, v in record.items() if k in ALLOWED_TELEMETRY_KEYS}
    sanitized["pedagogical_justification"] = EVENT_JUSTIFICATIONS[event_type]
    return sanitized
