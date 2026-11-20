"""
Configuración centralizada del Laboratorio 8: Simulación de Phishing y Evil-Twin
Organización ficticia: AndesCorp S.A. (andescorp.local)

IMPORTANTE: Todo el entorno es estrictamente ficticio, aislado a 127.0.0.1 / red local
de laboratorio y diseñado bajo el principio de Privacidad por Diseño (cero retención
de contraseñas en texto claro).
"""

from __future__ import annotations

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.environ.get("LAB8_DATA_DIR", BASE_DIR / "data"))
LOGS_DIR = Path(os.environ.get("LAB8_LOGS_DIR", BASE_DIR / "logs"))
MATERIALES_DIR = BASE_DIR / "materiales_formacion"
PLANTILLAS_DIR = BASE_DIR / "campana_correo" / "plantillas"
USUARIOS_FICTICIOS_PATH = BASE_DIR / "config" / "usuarios_ficticios.json"

# Asegurar directorios de ejecución
DATA_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Identidad de la organización ficticia
ORG_NAME = "AndesCorp S.A."
ORG_DOMAIN = "andescorp.local"
ALLOWED_EMAIL_DOMAINS = (ORG_DOMAIN,)  # Allowlist estricta: impide envíos a correos reales

# Identificador y clave efímera de campaña para pseudonimización HMAC-SHA256
CAMPAIGN_ID = os.environ.get("LAB8_CAMPAIGN_ID", "CAMP-2026-CONCIENTIZACION-SSO-01")
CAMPAIGN_HMAC_KEY = os.environ.get(
    "LAB8_HMAC_KEY",
    "andescorp-lab8-ephemeral-salt-2026-not-for-prod",
)

# Hosts y puertos de los servicios locales (bind exclusivo a loopback por defecto)
BIND_HOST = os.environ.get("LAB8_BIND_HOST", "127.0.0.1")
PUBLIC_HOST = os.environ.get("LAB8_PUBLIC_HOST", "127.0.0.1")

PORTAL_LEGITIMO_PORT = int(os.environ.get("PORTAL_LEGITIMO_PORT", "8001"))
PORTAL_EVIL_TWIN_PORT = int(os.environ.get("PORTAL_EVIL_TWIN_PORT", "8002"))
DASHBOARD_PORT = int(os.environ.get("DASHBOARD_PORT", "8003"))
WEBMAIL_PORT = int(os.environ.get("WEBMAIL_PORT", "8025"))
SMTP_PORT = int(os.environ.get("SMTP_PORT", "1025"))
SMTP_HOST = os.environ.get("SMTP_HOST", "127.0.0.1")

# URLs entre servicios (permiten override en Docker Compose)
PORTAL_LEGITIMO_URL = os.environ.get(
    "PORTAL_LEGITIMO_URL",
    f"http://{PUBLIC_HOST}:{PORTAL_LEGITIMO_PORT}",
)
PORTAL_EVIL_TWIN_URL = os.environ.get(
    "PORTAL_EVIL_TWIN_URL",
    f"http://{PUBLIC_HOST}:{PORTAL_EVIL_TWIN_PORT}",
)
DASHBOARD_URL = os.environ.get(
    "DASHBOARD_URL",
    f"http://{PUBLIC_HOST}:{DASHBOARD_PORT}",
)
WEBMAIL_URL = os.environ.get(
    "WEBMAIL_URL",
    f"http://{PUBLIC_HOST}:{WEBMAIL_PORT}",
)

# Dominios visibles simulados (para contexto didáctico de "lookalike")
LEGIT_DISPLAY_HOST = "sso.andescorp.local"
EVIL_TWIN_DISPLAY_HOST = "sso-andescorp-verificacion.local"

# Remitentes ficticios (exclusivamente dentro del entorno simulado)
SIM_SENDER_NAME = "Mesa de Ayuda TI - AndesCorp"
SIM_SENDER_EMAIL = "soporte-verificacion@andescorp-ti.local"
TRAINING_SENDER_NAME = "Seguridad de la Información y RR.HH. - AndesCorp S.A."
TRAINING_SENDER_EMAIL = "concientizacion@andescorp.local"
CSIRT_EMAIL = "csirt@andescorp.local"
CSIRT_EXTENSION = "Ext. 4911"

# Rutas de almacenamiento y logs
TELEMETRY_DB_PATH = DATA_DIR / "interactions.db"
MAIL_DB_PATH = DATA_DIR / "mail_server.db"
INTERACTIONS_LOG_PATH = LOGS_DIR / "interactions.jsonl"
SMTP_LOG_PATH = LOGS_DIR / "smtp_server.log"
MAIL_QUEUE_LOG_PATH = LOGS_DIR / "mail_queue.jsonl"
DESTRUCTION_AUDIT_PATH = DATA_DIR / "destruction_audit.json"

# Política de retención y privacidad
RETENTION_DAYS = 14
REDIRECT_COUNTDOWN_SECONDS = 12

# Campos estrictamente prohibidos en cualquier log, petición procesada o almacenamiento
FORBIDDEN_SENSITIVE_FIELDS = frozenset({
    "password",
    "passwd",
    "pwd",
    "pass",
    "contrasena",
    "contraseña",
    "clave",
    "secret",
    "pin",
    "otp",
    "mfa_code",
    "credential",
    "credencial",
    "authorization",
    "cookie",
})


def is_allowed_recipient(email_address: str) -> bool:
    """Valida que una dirección pertenezca exclusivamente a la allowlist ficticia."""
    if not email_address or "@" not in email_address:
        return False
    cleaned = email_address.strip().lower()
    if "<" in cleaned and ">" in cleaned:
        cleaned = cleaned.split("<", 1)[1].split(">", 1)[0].strip()
    domain = cleaned.rsplit("@", 1)[-1]
    return domain in ALLOWED_EMAIL_DOMAINS
