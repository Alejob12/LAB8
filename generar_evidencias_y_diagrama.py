"""
Generador de Diagrama de Arquitectura y Extractor de Evidencias de Ejecución (Lab 8).
Crea imágenes de alta calidad y extractos de logs estructurados para el Informe Técnico.
"""

import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = Path(__file__).resolve().parent
EVIDENCIAS_DIR = BASE_DIR / "evidencias"
EVIDENCIAS_DIR.mkdir(parents=True, exist_ok=True)


def extract_sample_logs():
    data_dir = BASE_DIR / "data"
    logs_dir = BASE_DIR / "logs"

    # 1. Copiar resumen de métricas
    from telemetria_privacidad.storage import TelemetryStore
    store = TelemetryStore()
    metrics = store.get_aggregated_metrics()
    (EVIDENCIAS_DIR / "resumen_metricas.json").write_text(
        json.dumps(metrics, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    # 2. Extracto de telemetría (primeras 15 líneas)
    t_log = logs_dir / "interactions.jsonl"
    if t_log.exists():
        lines = t_log.read_text(encoding="utf-8").strip().splitlines()
        sample = lines[-15:] if len(lines) > 15 else lines
        (EVIDENCIAS_DIR / "extracto_interactions.jsonl").write_text("\n".join(sample), encoding="utf-8")

    # 3. Extracto de logs SMTP
    s_log = logs_dir / "smtp_server.log"
    if s_log.exists():
        lines = s_log.read_text(encoding="utf-8").strip().splitlines()
        sample = lines[-20:] if len(lines) > 20 else lines
        (EVIDENCIAS_DIR / "extracto_smtp_server.log").write_text("\n".join(sample), encoding="utf-8")

    # 4. Extracto de cola de correos
    q_log = logs_dir / "mail_queue.jsonl"
    if q_log.exists():
        lines = q_log.read_text(encoding="utf-8").strip().splitlines()
        sample = lines[-15:] if len(lines) > 15 else lines
        (EVIDENCIAS_DIR / "extracto_mail_queue.jsonl").write_text("\n".join(sample), encoding="utf-8")

    print("[+] Extractos de evidencia guardados en carpeta 'evidencias/'.")


def generate_flow_diagram():
    # Dimensiones para diagrama de alta definición (ancho 1400 x alto 520)
    w, h = 1400, 520
    img = Image.new("RGB", (w, h), color="#FFFFFF")
    draw = ImageDraw.Draw(img)

    # Dibujar fondo sutil
    draw.rectangle([0, 0, w, h], fill="#F8FAFC")
    draw.rectangle([0, 0, w, 6], fill="#0F2942")

    # Título del Diagrama
    try:
        font_title = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 24)
        font_sub = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 15)
        font_box_title = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 16)
        font_box_text = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 13)
        font_tag = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 11)
    except Exception:
        font_title = font_sub = font_box_title = font_box_text = font_tag = ImageFont.load_default()

    draw.text((40, 24), "FLUJO INTEGRAL DEL LABORATORIO: PHISHING, EVIL-TWIN Y FORMACIÓN", fill="#0F2942", font=font_title)
    draw.text((40, 56), "Arquitectura cerrada en entorno aislado (127.0.0.1) bajo el principio de Privacidad por Diseño", fill="#64748B", font=font_sub)

    boxes = [
        {
            "num": "FASE 1",
            "title": "Correo Simulado",
            "subtitle": "Servidor SMTP :1025",
            "tag": "SEÑALES ROJAS",
            "color_top": "#B45309",
            "lines": [
                "• Lookalike: @andescorp-ti",
                "• Falsa urgencia (2 horas)",
                "• Enlace con token opaco",
                "• Allowlist estricta RFC 5321"
            ],
            "x": 40,
        },
        {
            "num": "FASE 2",
            "title": "Portal Evil-Twin",
            "subtitle": "Flask App :8002",
            "tag": "SUPLANTACIÓN",
            "color_top": "#B91C1C",
            "lines": [
                "• sso-andescorp-verificacion",
                "• GET -> LINK_CLICKED",
                "• Formulario de login falso",
                "• POST -> FORM_SUBMITTED"
            ],
            "x": 310,
        },
        {
            "num": "FASE 3",
            "title": "Privacidad por Diseño",
            "subtitle": "Sanitizador & Telemetría",
            "tag": "CERO CONTRASEÑAS",
            "color_top": "#15803D",
            "lines": [
                "• strip_sensitive_fields()",
                "• Contraseña descartada 0s",
                "• Pseudonimización HMAC",
                "• SQLite secure_delete=ON"
            ],
            "x": 580,
        },
        {
            "num": "FASE 4",
            "title": "Página Educativa",
            "subtitle": "Flask :8002 /educacion",
            "tag": "CONCIENTIZACIÓN",
            "color_top": "#D97706",
            "lines": [
                "• 4 banderas rojas explicadas",
                "• Correo formativo RR.HH.",
                "• Regla P.A.R.A. y Checklist",
                "• Cuenta regresiva (12 seg)"
            ],
            "x": 850,
        },
        {
            "num": "FASE 5",
            "title": "Portal Legítimo SSO",
            "subtitle": "Flask App :8001",
            "tag": "DESTINO SEGURO",
            "color_top": "#0F2942",
            "lines": [
                "• REDIRECTED_TO_LEGIT",
                "• sso.andescorp.local",
                "• ?from_simulation=1",
                "• Retención 14d + Purga"
            ],
            "x": 1120,
        },
    ]

    box_y = 100
    box_w = 240
    box_h = 360

    for i, b in enumerate(boxes):
        bx = b["x"]
        # Sombra
        draw.rounded_rectangle([bx + 4, box_y + 4, bx + box_w + 4, box_y + box_h + 4], radius=12, fill="#E2E8F0")
        # Tarjeta principal
        draw.rounded_rectangle([bx, box_y, bx + box_w, box_y + box_h], radius=12, fill="#FFFFFF", outline="#CBD5E1", width=2)
        # Encabezado de color
        draw.rounded_rectangle([bx, box_y, bx + box_w, box_y + 70], radius=12, fill=b["color_top"])
        draw.rectangle([bx, box_y + 58, bx + box_w, box_y + 70], fill=b["color_top"])  # aplanar esquinas inferiores del header

        # Textos de la cabecera
        draw.text((bx + 14, box_y + 12), b["num"], fill="#FBBF24", font=font_tag)
        draw.text((bx + 14, box_y + 28), b["title"], fill="#FFFFFF", font=font_box_title)
        draw.text((bx + 14, box_y + 48), b["subtitle"], fill="#E2E8F0", font=font_tag)

        # Tag
        draw.rounded_rectangle([bx + 14, box_y + 82, bx + box_w - 14, box_y + 104], radius=6, fill="#F1F5F9", outline="#E2E8F0")
        draw.text((bx + 20, box_y + 86), b["tag"], fill="#334155", font=font_tag)

        # Líneas descriptivas
        ly = box_y + 124
        for line in b["lines"]:
            draw.text((bx + 14, ly), line, fill="#334155", font=font_box_text)
            ly += 30

        # Conector flecha hacia el siguiente paso
        if i < len(boxes) - 1:
            ax = bx + box_w + 6
            ay = box_y + (box_h // 2) - 10
            draw.line([ax, ay, ax + 18, ay], fill="#94A3B8", width=4)
            draw.polygon([(ax + 18, ay - 6), (ax + 26, ay), (ax + 18, ay + 6)], fill="#94A3B8")

    # Pie del diagrama
    draw.rectangle([0, h - 35, w, h], fill="#0F2942")
    draw.text((40, h - 24), "Universidad de los Andes · Ciberseguridad · Laboratorio 8 (Phishing y Evil-Twin) · Entorno 100% Simulado", fill="#CBD5E1", font=font_tag)

    diagram_path = EVIDENCIAS_DIR / "diagrama_flujo.png"
    img.save(diagram_path, "PNG", dpi=(300, 300))
    print(f"[+] Diagrama generado exitosamente en: {diagram_path}")


if __name__ == "__main__":
    extract_sample_logs()
    generate_flow_diagram()
