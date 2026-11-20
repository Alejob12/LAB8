"""
Orquestador Central del Laboratorio 8: Phishing y Evil Twin (AndesCorp S.A.)

Permite gestionar, desplegar y auditar todos los componentes del laboratorio:
- Servidor SMTP Local (puerto 1025)
- Portal Legítimo SSO (puerto 8001)
- Portal Simulado Evil-Twin (puerto 8002)
- Dashboard de Telemetría (puerto 8003)
- Webmail Corporativo (puerto 8025)

Uso:
  python run_lab.py start                 Arranca todos los servicios en segundo plano
  python run_lab.py stop                  Detiene todos los servicios locales
  python run_lab.py status                Verifica el estado de salud de los 5 servicios
  python run_lab.py send-campaign         Despacha la campaña a los 8 usuarios ficticios
  python run_lab.py simulate-activity     Simula interacciones realistas de colaboradores
  python run_lab.py purge --confirm       Ejecuta la destrucción segura de datos
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import requests

from campana_correo.despachador import preparar_y_enviar_campana
from config.settings import (
    BIND_HOST,
    DASHBOARD_PORT,
    DASHBOARD_URL,
    PORTAL_EVIL_TWIN_PORT,
    PORTAL_EVIL_TWIN_URL,
    PORTAL_LEGITIMO_PORT,
    PORTAL_LEGITIMO_URL,
    SMTP_PORT,
    WEBMAIL_PORT,
    WEBMAIL_URL,
)
from telemetria_privacidad.purga_segura import execute_secure_purge
from telemetria_privacidad.storage import TelemetryStore

PID_FILE = Path(__file__).resolve().parent / "data" / ".services_pids.json"


SERVICES = {
    "smtp_local": {
        "name": "Servidor SMTP Local",
        "cmd": [sys.executable, "-m", "servidor_correo.smtp_local"],
        "port": SMTP_PORT,
        "health_url": None,
    },
    "portal_legitimo": {
        "name": "Portal SSO Legítimo",
        "cmd": [sys.executable, "-m", "portal_legitimo.app"],
        "port": PORTAL_LEGITIMO_PORT,
        "health_url": f"{PORTAL_LEGITIMO_URL}/health",
    },
    "portal_evil_twin": {
        "name": "Portal Evil-Twin Simulado",
        "cmd": [sys.executable, "-m", "portal_evil_twin.app"],
        "port": PORTAL_EVIL_TWIN_PORT,
        "health_url": f"{PORTAL_EVIL_TWIN_URL}/health",
    },
    "webmail_app": {
        "name": "Webmail Corporativo",
        "cmd": [sys.executable, "-m", "servidor_correo.webmail_app"],
        "port": WEBMAIL_PORT,
        "health_url": f"{WEBMAIL_URL}/health",
    },
    "dashboard_app": {
        "name": "Dashboard de Telemetría",
        "cmd": [sys.executable, "-m", "telemetria_privacidad.dashboard_app"],
        "port": DASHBOARD_PORT,
        "health_url": f"{DASHBOARD_URL}/health",
    },
}


def _save_pids(pids: dict[str, int]) -> None:
    PID_FILE.parent.mkdir(parents=True, exist_ok=True)
    PID_FILE.write_text(json.dumps(pids, indent=2), encoding="utf-8")


def _load_pids() -> dict[str, int]:
    if not PID_FILE.exists():
        return {}
    try:
        return json.loads(PID_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def is_process_running(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def start_services() -> None:
    """Arranca todos los servicios en segundo plano."""
    current_pids = _load_pids()
    new_pids: dict[str, int] = {}

    print("=" * 70)
    print(" INICIANDO ENTORNO CONTROLADO DE LABORATORIO 8 — ANDESCORP S.A.")
    print("=" * 70)

    for key, svc in SERVICES.items():
        existing_pid = current_pids.get(key)
        if existing_pid and is_process_running(existing_pid):
            print(f" [OK] {svc['name']} ya se encuentra activo (PID {existing_pid}).")
            new_pids[key] = existing_pid
            continue

        env = os.environ.copy()
        env["PYTHONPATH"] = str(Path(__file__).resolve().parent)

        proc = subprocess.Popen(
            svc["cmd"],
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        new_pids[key] = proc.pid
        print(f" [+] {svc['name']} iniciado en segundo plano (PID {proc.pid}, puerto {svc['port']}).")

    _save_pids(new_pids)
    print("\nEsperando inicialización de servicios...")
    time.sleep(2)
    check_status()

    print("\nEnlaces de acceso directo:")
    print(f" • Webmail Corporativo:      {WEBMAIL_URL}")
    print(f" • Portal SSO Legítimo:     {PORTAL_LEGITIMO_URL}")
    print(f" • Portal Evil-Twin:         {PORTAL_EVIL_TWIN_URL}")
    print(f" • Dashboard Telemetría:     {DASHBOARD_URL}")
    print("=" * 70)


def stop_services() -> None:
    """Detiene todos los servicios registrados."""
    pids = _load_pids()
    if not pids:
        print("No se encontraron procesos activos registrados.")
        return

    print("Deteniendo servicios del laboratorio...")
    for key, pid in pids.items():
        if is_process_running(pid):
            try:
                os.kill(pid, signal.SIGTERM)
                print(f" [x] {SERVICES.get(key, {}).get('name', key)} (PID {pid}) detenido.")
            except Exception as e:
                print(f" [!] Error al detener PID {pid}: {e}")
        else:
            print(f" [-] PID {pid} ({key}) no estaba en ejecución.")

    if PID_FILE.exists():
        PID_FILE.unlink()
    print("Todos los servicios fueron detenidos.")


def check_status() -> bool:
    """Verifica el estado de los servicios."""
    pids = _load_pids()
    print("\nESTADO DE LOS SERVICIOS:")
    print("-" * 65)

    all_ok = True
    for key, svc in SERVICES.items():
        pid = pids.get(key)
        running = pid and is_process_running(pid)

        health_ok = True
        if svc["health_url"]:
            try:
                r = requests.get(svc["health_url"], timeout=2)
                health_ok = (r.status_code == 200)
            except Exception:
                health_ok = False

        status_str = "ACTIVO" if (running and health_ok) else "INACTIVO / ERROR"
        icon = "✓" if (running and health_ok) else "✗"
        if not (running and health_ok):
            all_ok = False

        print(f" {icon} {svc['name']:<28} Puerto: {svc['port']:<6} PID: {str(pid):<7} Estado: {status_str}")

    print("-" * 65)
    return all_ok


def dispatch_campaign() -> None:
    """Despacha la campaña simulada a los usuarios ficticios."""
    print("\nDespachando campaña de concientización a través del servidor Mail local...")
    res = preparar_y_enviar_campana()
    print(f"Total de correos preparados y despachados: {res['total_dispatched']}")
    for r in res["results"]:
        print(f" • {r['user']} ({r['name']}) -> Estado: {r['status']} (Queue ID: {r['queue_id']})")
    print("\nCampaña despachada con éxito. Puedes revisar la bandeja en http://127.0.0.1:8025.")


def simulate_activity() -> None:
    """Simula una interacción gradual y realista de los colaboradores ficticios."""
    print("\nSimulando interacción pedagógica de colaboradores con la campaña...")
    store = TelemetryStore()
    tokens = []

    with store._connect() as conn:
        rows = conn.execute("SELECT * FROM campaign_tokens").fetchall()
        tokens = [dict(r) for r in rows]

    if not tokens:
        print("[!] No se encontraron participantes registrados. Ejecuta 'python run_lab.py send-campaign' primero.")
        return

    # Escenarios pedagógicos:
    # 1. 2 participantes no hacen clic (alta concientización preventiva)
    # 2. 2 participantes hacen clic pero cierran la ventana (sospecharon de la URL)
    # 3. 4 participantes completan el formulario, reciben correo formativo, leen la página educativa y son redirigidos

    actions = [
        {"click": True, "submit": True},   # EMP 1
        {"click": True, "submit": False},  # EMP 2
        {"click": True, "submit": True},   # EMP 3
        {"click": False, "submit": False}, # EMP 4
        {"click": True, "submit": True},   # EMP 5
        {"click": False, "submit": False}, # EMP 6
        {"click": True, "submit": True},   # EMP 7
        {"click": True, "submit": False},  # EMP 8
    ]

    session = requests.Session()

    for idx, p in enumerate(tokens):
        plan = actions[idx % len(actions)]
        token = p["token"]
        name = p["recipient_name"]
        email = p["recipient_email"]

        print(f"\n[Participante] {name} ({email}):")

        if not plan["click"]:
            print("  -> No interactuó con el enlace del correo (comportamiento seguro).")
            continue

        # Simular clic en el enlace
        click_url = f"{PORTAL_EVIL_TWIN_URL}/login?t={token}"
        try:
            r1 = session.get(click_url, timeout=3)
            print(f"  -> Clic en enlace simulado: {click_url} (HTTP {r1.status_code})")
        except Exception as e:
            print(f"  -> Error al acceder al evil-twin: {e}")
            continue

        if not plan["submit"]:
            print("  -> Inspeccionó la URL 'sso-andescorp-verificacion.local', detectó la anomalía y cerró la pestaña.")
            continue

        # Simular ingreso de contraseña y envío de formulario
        print("  -> Ingresó credenciales en el portal falso. Enviando formulario...")
        try:
            r2 = session.post(
                click_url,
                data={
                    "token": token,
                    "email": email,
                    "password": "PasswordFicticio123!",
                },
                allow_redirects=False,
                timeout=3,
            )
            print(f"  -> Formulario enviado (HTTP {r2.status_code}). Contraseña descartada al instante en memoria.")

            # Simular visualización de la página educativa
            edu_url = f"{PORTAL_EVIL_TWIN_URL}/educacion?t={token}"
            r3 = session.get(edu_url, timeout=3)
            print(f"  -> Leyó la página educativa post-interacción (HTTP {r3.status_code}).")

            # Simular redirección al portal legítimo
            redir_url = f"{PORTAL_EVIL_TWIN_URL}/redirigir-legitimo?t={token}"
            r4 = session.get(redir_url, allow_redirects=False, timeout=3)
            dest_legit = r4.headers.get("Location", "")
            print(f"  -> Redirigido automáticamente al portal legítimo: {dest_legit}")

            # Acceso final al portal legítimo
            if dest_legit:
                r5 = session.get(dest_legit, timeout=3)
                print(f"  -> Llegada confirmada al portal legítimo (HTTP {r5.status_code}).")

        except Exception as e:
            print(f"  -> Error durante la interacción: {e}")

    print("\n" + "=" * 70)
    print(" Simulación de interacciones completada con éxito.")
    print(" Consulta los resultados en vivo en el Dashboard: http://127.0.0.1:8003")
    print("=" * 70)


def main() -> None:
    parser = argparse.ArgumentParser(description="Gestor y orquestador del Laboratorio 8 (AndesCorp S.A.)")
    subparsers = parser.add_subparsers(dest="command", help="Comando a ejecutar")

    subparsers.add_parser("start", help="Iniciar todos los servicios del laboratorio")
    subparsers.add_parser("stop", help="Detener todos los servicios del laboratorio")
    subparsers.add_parser("status", help="Consultar estado de salud de los servicios")
    subparsers.add_parser("send-campaign", help="Despachar campaña de simulación")
    subparsers.add_parser("simulate-activity", help="Simular interacción de los colaboradores")

    purge_parser = subparsers.add_parser("purge", help="Ejecutar eliminación segura de datos")
    purge_parser.add_argument("--confirm", action="store_true", required=True, help="Confirmación de borrado seguro")
    purge_parser.add_argument("--keep-mail", action="store_true", help="Mantener correos en la bandeja")

    args = parser.parse_args()

    if args.command == "start":
        start_services()
    elif args.command == "stop":
        stop_services()
    elif args.command == "status":
        check_status()
    elif args.command == "send-campaign":
        dispatch_campaign()
    elif args.command == "simulate-activity":
        simulate_activity()
    elif args.command == "purge":
        cert = execute_secure_purge(include_mail=not args.keep_mail)
        print("\nCertificado de Destrucción de Datos Emitido:")
        print(json.dumps(cert, indent=2, ensure_ascii=False))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
