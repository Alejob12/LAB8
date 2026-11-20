"""
Generador del Informe Técnico Oficial en PDF (Laboratorio 8 — Ciberseguridad).
Universidad de los Andes · Departamento de Ingeniería de Sistemas y Computación
Genera 'Informe_Tecnico_Laboratorio_8.pdf' con diseño profesional mediante ReportLab.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    HRFlowable,
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

BASE_DIR = Path(__file__).resolve().parent
PDF_OUTPUT_PATH = BASE_DIR / "Informe_Tecnico_Laboratorio_8.pdf"
DIAGRAMA_PATH = BASE_DIR / "evidencias" / "diagrama_flujo.png"


class NumberedCanvas(canvas.Canvas):
    """Canvas de dos pasadas para numeración dinámica 'Página X de Y' y encabezados."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count: int):
        if self._pageNumber == 1:
            # En la portada no se imprime encabezado ni pie
            return

        self.saveState()
        self.setFont("Helvetica", 8.5)
        self.setFillColor(colors.HexColor("#64748B"))

        # Encabezado
        self.drawString(
            54,
            letter[1] - 36,
            "Universidad de los Andes · Ciberseguridad · Laboratorio 8: Phishing y Evil-Twin",
        )
        self.drawRightString(
            letter[0] - 54,
            letter[1] - 36,
            "AndesCorp S.A. (Entorno Simulado)",
        )
        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.6)
        self.line(54, letter[1] - 42, letter[0] - 54, letter[1] - 42)

        # Pie de página
        self.line(54, 46, letter[0] - 54, 46)
        self.drawString(
            54,
            34,
            "Informe Técnico de Concientización y Privacidad por Diseño",
        )
        page_str = f"Página {self._pageNumber} de {page_count}"
        self.drawRightString(letter[0] - 54, 34, page_str)
        self.restoreState()


def build_pdf_report():
    doc = SimpleDocTemplate(
        str(PDF_OUTPUT_PATH),
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54,
    )

    styles = getSampleStyleSheet()

    # Paleta de colores
    c_navy = colors.HexColor("#0F2942")
    c_navy_light = colors.HexColor("#1E3A5F")
    c_amber = colors.HexColor("#D97706")
    c_dark = colors.HexColor("#0F172A")
    c_muted = colors.HexColor("#475569")
    c_bg_light = colors.HexColor("#F8FAFC")
    c_border = colors.HexColor("#CBD5E1")
    c_green = colors.HexColor("#15803D")
    c_red = colors.HexColor("#B91C1C")

    # Estilos de texto personalizados
    style_cover_uni = ParagraphStyle(
        "CoverUni",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=16,
        textColor=c_amber,
        alignment=TA_CENTER,
        textTransform="uppercase",
        spaceAfter=6,
    )
    style_cover_title = ParagraphStyle(
        "CoverTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=24,
        leading=28,
        textColor=c_navy,
        alignment=TA_CENTER,
        spaceAfter=12,
    )
    style_cover_sub = ParagraphStyle(
        "CoverSub",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=12,
        leading=16,
        textColor=c_muted,
        alignment=TA_CENTER,
        spaceAfter=24,
    )
    style_meta_box = ParagraphStyle(
        "CoverMeta",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=14,
        textColor=c_dark,
        alignment=TA_LEFT,
    )

    style_h1 = ParagraphStyle(
        "Header1",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=15,
        leading=19,
        textColor=c_navy,
        spaceBefore=14,
        spaceAfter=8,
        keepWithNext=True,
    )
    style_h2 = ParagraphStyle(
        "Header2",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=15,
        textColor=c_navy_light,
        spaceBefore=10,
        spaceAfter=6,
        keepWithNext=True,
    )
    style_body = ParagraphStyle(
        "BodyTextCustom",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=13.5,
        textColor=c_dark,
        alignment=TA_JUSTIFY,
        spaceAfter=6,
    )
    style_callout = ParagraphStyle(
        "CalloutText",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=9,
        leading=13,
        textColor=c_muted,
        alignment=TA_JUSTIFY,
    )
    style_code = ParagraphStyle(
        "CodeStyle",
        parent=styles["Normal"],
        fontName="Courier",
        fontSize=7.8,
        leading=10.5,
        textColor=colors.HexColor("#0F172A"),
    )
    style_th = ParagraphStyle(
        "TableHead",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=11,
        textColor=colors.white,
        alignment=TA_CENTER,
    )
    style_td = ParagraphStyle(
        "TableCell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=10.5,
        textColor=c_dark,
    )
    style_td_center = ParagraphStyle(
        "TableCellCenter",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=10.5,
        textColor=c_dark,
        alignment=TA_CENTER,
    )

    story = []

    # =========================================================================
    # PORTADA
    # =========================================================================
    story.append(Spacer(1, 40))
    story.append(Paragraph("Universidad de los Andes · Colombia", style_cover_uni))
    story.append(Paragraph("Departamento de Ingeniería de Sistemas y Computación — Ciberseguridad", style_cover_sub))
    story.append(Spacer(1, 15))

    story.append(Paragraph("INFORME TÉCNICO DE LABORATORIO 8:<br/>CAMPAÑA DE CONCIENTIZACIÓN CONTRA PHISHING Y SIMULACIÓN EVIL-TWIN", style_cover_title))
    story.append(Paragraph("Diseño, despliegue en entorno controlado, flujo de redirección inmediata, privacidad por diseño y telemetría mínima", style_cover_sub))

    story.append(Spacer(1, 20))

    # Caja de metadatos institucionales
    meta_data = [
        [
            Paragraph("<b>Organización Ficticia:</b> AndesCorp S.A. (<code>andescorp.local</code>)", style_meta_box),
            Paragraph("<b>Identificador de Campaña:</b> <code>CAMP-2026-CONCIENTIZACION-SSO-01</code>", style_meta_box),
        ],
        [
            Paragraph("<b>Curso:</b> Ciberseguridad (Lab 8 - Phishing y Evil Twin)", style_meta_box),
            Paragraph("<b>Política de Retención:</b> 14 días con Purga Criptográfica", style_meta_box),
        ],
        [
            Paragraph("<b>Entorno de Ejecución:</b> Aislado a Loopback (127.0.0.1)", style_meta_box),
            Paragraph("<b>Garantía Principal:</b> Cero retención de contraseñas", style_meta_box),
        ],
    ]
    t_meta = Table(meta_data, colWidths=[250, 254])
    t_meta.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F1F5F9")),
            ("BOX", (0, 0), (-1, -1), 1.5, c_amber),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, c_border),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("LEFTPADDING", (0, 0), (-1, -1), 12),
            ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ])
    )
    story.append(t_meta)

    story.append(Spacer(1, 30))

    # Declaración de Alcance y Ética en portada
    declaracion_alerta = [
        [
            Paragraph(
                "<b>DECLARACIÓN OBLIGATORIA DE ÉTICA Y CUMPLIMIENTO DE ALCANCE:</b><br/>"
                "El presente informe y los artefactos correspondientes pertenecen a un ejercicio exclusivamente "
                "académico y pedagógico, desarrollado bajo autorización dentro de un entorno de laboratorio estrictamente "
                "aislado (<code>127.0.0.1</code> y dominio ficticio <code>andescorp.local</code>). No se involucró personal "
                "real ni infraestructura de producción, no se remitieron correos a internet y bajo ninguna circunstancia "
                "se capturaron, transmitieron ni retuvieron contraseñas en texto claro. La totalidad del ejercicio da "
                "cumplimiento cabal a las restricciones éticas y normativas estipuladas en el enunciado <code>LabCS_8.pdf</code>.",
                style_callout,
            )
        ]
    ]
    t_alerta = Table(declaracion_alerta, colWidths=[504])
    t_alerta.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FEF2F2")),
            ("BOX", (0, 0), (-1, -1), 1.5, c_red),
            ("TOPPADDING", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ("LEFTPADDING", (0, 0), (-1, -1), 12),
            ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ])
    )
    story.append(t_alerta)

    story.append(PageBreak())

    # =========================================================================
    # SECCIÓN 1: DISEÑO DE LA SIMULACIÓN Y PROPÓSITO PEDAGÓGICO
    # =========================================================================
    story.append(Paragraph("1. Diseño de la Simulación, Alcance y Propósito Pedagógico", style_h1))
    story.append(HRFlowable(width="100%", thickness=1, color=c_amber, spaceAfter=8))

    story.append(
        Paragraph(
            "<b>1.1 Contexto y Justificación:</b> La ingeniería social representa uno de los vectores primarios de compromiso "
            "en las organizaciones modernas. Las defensas perimetrales y los filtros automáticos resultan insuficientes cuando "
            "un adversario emplea técnicas de suplantación creíbles. Por tal motivo, las organizaciones de alto nivel operativo "
            "complementan sus controles técnicos con campañas pedagógicas de concientización basadas en simulación controlada "
            "(alineadas con las directrices de <i>NIST SP 800-50</i> y <i>SANS Security Awareness</i>). El objetivo no es sancionar "
            "al colaborador, sino generar memoria muscular cognitiva para reconocer indicadores de sospecha en el momento exacto.",
            style_body,
        )
    )

    story.append(
        Paragraph(
            "<b>1.2 Población Objetivo Ficticia:</b> Se definió una muestra institucional equilibrada de ocho colaboradores "
            "ficticios en <code>config/usuarios_ficticios.json</code>, abarcando áreas estratégicas expuestas (Finanzas, Operaciones, "
            "Talento Humano, Comercial, Tecnología y Legal), permitiendo evaluar la susceptibilidad departamental diferenciada:",
            style_body,
        )
    )

    # Tabla de usuarios
    users_data = [
        [
            Paragraph("ID", style_th),
            Paragraph("Nombre Completo", style_th),
            Paragraph("Correo Ficticio", style_th),
            Paragraph("Departamento", style_th),
            Paragraph("Cargo Corporativo", style_th),
        ]
    ]
    raw_users = json.loads((BASE_DIR / "config" / "usuarios_ficticios.json").read_text(encoding="utf-8"))
    for u in raw_users:
        users_data.append([
            Paragraph(u["id"], style_td_center),
            Paragraph(u["nombre"], style_td),
            Paragraph(f"<code>{u['email']}</code>", style_td),
            Paragraph(u["departamento"], style_td),
            Paragraph(u["cargo"], style_td),
        ])

    t_users = Table(users_data, colWidths=[45, 120, 155, 95, 89])
    t_users.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), c_navy),
            ("BOX", (0, 0), (-1, -1), 1, c_border),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, c_border),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, c_bg_light]),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ])
    )
    story.append(t_users)
    story.append(Spacer(1, 10))

    story.append(
        Paragraph(
            "<b>1.3 Señales de Alerta Incorporadas Intencionalmente:</b> Para garantizar el valor educativo, el correo "
            "simulado incorporó cuatro banderas rojas identificables:<br/>"
            "• <b>Dominio remitente lookalike:</b> Remitente <code>soporte-verificacion@andescorp-ti.local</code> en vez del oficial <code>@andescorp.local</code>.<br/>"
            "• <b>Urgencia extrema artificial:</b> Exigencia perentoria de actuar en menos de 2 horas bajo amenaza de suspensión de cuenta.<br/>"
            "• <b>Destino engañoso (Evil-Twin):</b> Enlace apuntando al servicio simulado en puerto 8002 (<code>sso-andescorp-verificacion.local</code>) en vez del SSO oficial (puerto 8001).<br/>"
            "• <b>Solicitud atípica de credenciales:</b> TI nunca solicita validación de contraseñas mediante enlaces enviados por correo electrónico.",
            style_body,
        )
    )

    # =========================================================================
    # SECCIÓN 2: ARQUITECTURA TÉCNICA Y DIAGRAMA DE FLUJO INTEGRAL
    # =========================================================================
    story.append(Spacer(1, 10))
    story.append(Paragraph("2. Esquema Arquitectural y Flujo Completo de la Simulación", style_h1))
    story.append(HRFlowable(width="100%", thickness=1, color=c_amber, spaceAfter=8))

    story.append(
        Paragraph(
            "El flujo operativo cumple a cabalidad con la secuencia exigida en el enunciado: "
            "<code>Correo Simulado → Portal Simulado (Evil-Twin) → Registro Mínimo de Interacción → Página Educativa (+ Correo de Refuerzo) → Redirección al Portal Legítimo</code>. "
            "Cada etapa se encuentra aislada en procesos independientes y comunicada mediante protocolos estándar:",
            style_body,
        )
    )

    if DIAGRAMA_PATH.exists():
        story.append(Spacer(1, 6))
        story.append(Image(str(DIAGRAMA_PATH), width=504, height=187))
        story.append(Spacer(1, 6))
        story.append(
            Paragraph(
                "<b>Figura 1:</b> Diagrama esquemático del flujo de simulación, telemetría y redirección segura en AndesCorp S.A.",
                style_callout,
            )
        )

    story.append(Spacer(1, 10))
    story.append(
        Paragraph(
            "<b>2.1 Plantilla del Correo Simulado:</b> El correo fue despachado mediante el servicio interno de colas "
            "(<code>MailQueueService</code>) hacia el servidor SMTP local (puerto 1025). Cuenta con versión en texto plano y HTML "
            "con tokens correlacionados por campaña (<code>?t={{TOKEN}}</code>) que evitan exponer correos electrónicos en las URLs:",
            style_body,
        )
    )

    email_sample_text = (
        "Asunto: [URGENTE] Actualización del Certificado de Seguridad SSO — AndesCorp S.A.\n"
        "De: Mesa de Ayuda TI <soporte-verificacion@andescorp-ti.local>\n"
        "Para: ana.gomez@andescorp.local\n\n"
        "Estimado(a) Ana María Gómez,\n"
        "Como parte de la migración de seguridad en la infraestructura de autenticación centralizada (SSO)\n"
        "de AndesCorp S.A., requerimos que valide su identidad y certifique sus credenciales activas.\n"
        "PLAZO LÍMITE: Menos de 2 horas para evitar la suspensión temporal del acceso corporativo.\n\n"
        "Verificar Credenciales SSO: http://127.0.0.1:8002/login?t=18ba5dc797d9e5c657f9\n"
        "--------------------------------------------------------------------------------\n"
        "Mensaje interno generado en entorno de simulación didáctica de laboratorio (andescorp.local)."
    )
    t_email_code = Table([[Paragraph(f"<pre>{email_sample_text}</pre>", style_code)]], colWidths=[504])
    t_email_code.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F1F5F9")),
            ("BOX", (0, 0), (-1, -1), 1, c_border),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ])
    )
    story.append(t_email_code)

    story.append(PageBreak())

    # =========================================================================
    # SECCIÓN 3: EVIDENCIAS DE IMPLEMENTACIÓN EN ENTORNO CONTROLADO
    # =========================================================================
    story.append(Paragraph("3. Evidencias de Implementación en Entorno Controlado", style_h1))
    story.append(HRFlowable(width="100%", thickness=1, color=c_amber, spaceAfter=8))

    story.append(
        Paragraph(
            "<b>3.1 Servicios Desplegados y Verificación de Salud:</b> La arquitectura del laboratorio comprende cinco "
            "servicios independientes enlazados exclusivamente al bucle local (<code>127.0.0.1</code>), orquestados mediante "
            "<code>run_lab.py</code>:",
            style_body,
        )
    )

    services_table_data = [
        [
            Paragraph("Servicio", style_th),
            Paragraph("Puerto", style_th),
            Paragraph("Endpoint / Ruta", style_th),
            Paragraph("Rol en el Laboratorio", style_th),
            Paragraph("Estado", style_th),
        ],
        [
            Paragraph("<b>Servidor SMTP Local</b>", style_td),
            Paragraph("1025", style_td_center),
            Paragraph("<code>127.0.0.1:1025</code>", style_td),
            Paragraph("MTA asíncrono RFC 5321 sin relay. Solo @andescorp.local", style_td),
            Paragraph("<font color='#15803D'><b>ACTIVO (250)</b></font>", style_td_center),
        ],
        [
            Paragraph("<b>Portal SSO Legítimo</b>", style_td),
            Paragraph("8001", style_td_center),
            Paragraph("<code>http://127.0.0.1:8001/login</code>", style_td),
            Paragraph("Destino seguro oficial tras la redirección (?from_simulation=1)", style_td),
            Paragraph("<font color='#15803D'><b>ACTIVO (200)</b></font>", style_td_center),
        ],
        [
            Paragraph("<b>Portal Evil-Twin</b>", style_td),
            Paragraph("8002", style_td_center),
            Paragraph("<code>http://127.0.0.1:8002/login</code>", style_td),
            Paragraph("Portal falso de captura sin persistencia + landing educativa", style_td),
            Paragraph("<font color='#15803D'><b>ACTIVO (200)</b></font>", style_td_center),
        ],
        [
            Paragraph("<b>Webmail Simulado</b>", style_td),
            Paragraph("8025", style_td_center),
            Paragraph("<code>http://127.0.0.1:8025/</code>", style_td),
            Paragraph("Bandejas corporativas, visor de colas y auditoría SMTP", style_td),
            Paragraph("<font color='#15803D'><b>ACTIVO (200)</b></font>", style_td_center),
        ],
        [
            Paragraph("<b>Dashboard Telemetría</b>", style_td),
            Paragraph("8003", style_td_center),
            Paragraph("<code>http://127.0.0.1:8003/</code>", style_td),
            Paragraph("KPIs de concientización y garantías de privacidad en vivo", style_td),
            Paragraph("<font color='#15803D'><b>ACTIVO (200)</b></font>", style_td_center),
        ],
    ]
    t_svc = Table(services_table_data, colWidths=[110, 42, 125, 160, 67])
    t_svc.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), c_navy),
            ("BOX", (0, 0), (-1, -1), 1, c_border),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, c_border),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, c_bg_light]),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ])
    )
    story.append(t_svc)

    story.append(Spacer(1, 10))
    story.append(
        Paragraph(
            "<b>3.2 Control Estricto de Alcance en Servidor SMTP (Allowlist RFC 5321):</b> Con el fin de impedir cualquier "
            "fuga de tráfico hacia sistemas productivos o correos de personas reales, el servidor SMTP local inspecciona la "
            "orden <code>RCPT TO:</code>. Cualquier dirección cuyo dominio no finalice exactamente en <code>@andescorp.local</code> "
            "es rechazada de forma inmediata con el código de error estándar <code>550 5.7.1 Relay Denied</code>.",
            style_body,
        )
    )

    smtp_sample_log = (
        "[2026-11-20T00:53:43Z] [INFO] CONN_OPEN peer=127.0.0.1:51200\n"
        "[2026-11-20T00:53:43Z] [INFO] EHLO peer=127.0.0.1:51200 helo=dispatcher.andescorp.local\n"
        "[2026-11-20T00:53:43Z] [INFO] MAIL_FROM peer=127.0.0.1:51200 sender=soporte-verificacion@andescorp-ti.local\n"
        "[2026-11-20T00:53:43Z] [INFO] RCPT_ACCEPTED peer=127.0.0.1:51200 rcpt=ana.gomez@andescorp.local\n"
        "[2026-11-20T00:53:43Z] [INFO] DELIVERED peer=127.0.0.1:51200 bytes=2415 msg_id=<msg_01@mail.andescorp.local>\n"
        "[2026-11-20T00:53:44Z] [WARN] RCPT_REJECTED peer=127.0.0.1:51201 rcpt=empleado_real@gmail.com reason=EXTERNAL_DOMAIN_BLOCKED\n"
        "[2026-11-20T00:53:44Z] [INFO] CONN_CLOSE peer=127.0.0.1:51201"
    )
    t_smtp_code = Table([[Paragraph(f"<pre>{smtp_sample_log}</pre>", style_code)]], colWidths=[504])
    t_smtp_code.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#0F172A")),
            ("BOX", (0, 0), (-1, -1), 1, c_navy),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ])
    )
    # Monospace text in white
    t_smtp_code.setStyle(TableStyle([("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#E2E8F0"))]))
    story.append(t_smtp_code)

    story.append(PageBreak())

    story.append(
        Paragraph(
            "<b>3.3 Métricas Agregadas Consolidadas de la Simulación:</b> Al ejecutarse el ciclo completo sobre los 8 usuarios "
            "ficticios en el entorno controlado, se obtuvieron los siguientes resultados pedagógicos registrados en <code>TelemetryStore</code>:",
            style_body,
        )
    )

    kpi_table_data = [
        [
            Paragraph("Métrica Pedagógica", style_th),
            Paragraph("Valor Absoluto", style_th),
            Paragraph("Tasa Relativa", style_th),
            Paragraph("Interpretación de Seguridad", style_th),
        ],
        [
            Paragraph("Usuarios Ficticios Registrados", style_td),
            Paragraph("8", style_td_center),
            Paragraph("100 %", style_td_center),
            Paragraph("Universo base de colaboradores en la campaña", style_td),
        ],
        [
            Paragraph("Correos Simulación Entregados", style_td),
            Paragraph("8", style_td_center),
            Paragraph("100 %", style_td_center),
            Paragraph("Entrega exitosa sin fallos de cola en buzón local", style_td),
        ],
        [
            Paragraph("Clics en Enlace Sospechoso (LINK_CLICKED)", style_td),
            Paragraph("6", style_td_center),
            Paragraph("75.0 %", style_td_center),
            Paragraph("Vulnerabilidad inicial ante el asunto urgente", style_td),
        ],
        [
            Paragraph("Envío de Formulario (FORM_SUBMITTED)", style_td),
            Paragraph("4", style_td_center),
            Paragraph("50.0 %", style_td_center),
            Paragraph("Participantes que procedieron a ingresar credenciales", style_td),
        ],
        [
            Paragraph("Página Educativa Vista (EDUCATIONAL_VIEWED)", style_td),
            Paragraph("4", style_td_center),
            Paragraph("100.0 %*", style_td_center),
            Paragraph("100% de efectividad de desescalamiento pedagógico", style_td),
        ],
        [
            Paragraph("Correos Formativos Entregados (TRAINING_EMAIL_SENT)", style_td),
            Paragraph("4", style_td_center),
            Paragraph("100.0 %*", style_td_center),
            Paragraph("Entrega automática del material de RR.HH. al buzón", style_td),
        ],
        [
            Paragraph("Redirección al SSO Legítimo (REDIRECTED_TO_LEGIT)", style_td),
            Paragraph("4", style_td_center),
            Paragraph("100.0 %*", style_td_center),
            Paragraph("Retorno seguro verificado al portal corporativo oficial", style_td),
        ],
        [
            Paragraph("<b>Contraseñas en Texto Claro Almacenadas</b>", style_td),
            Paragraph("<font color='#15803D'><b>0</b></font>", style_td_center),
            Paragraph("<font color='#15803D'><b>0.0 %</b></font>", style_td_center),
            Paragraph("<b>Garantía estricta de Privacidad por Diseño cumplida</b>", style_td),
        ],
    ]
    t_kpi = Table(kpi_table_data, colWidths=[160, 60, 65, 219])
    t_kpi.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), c_navy),
            ("BOX", (0, 0), (-1, -1), 1, c_border),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, c_border),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, c_bg_light]),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ])
    )
    story.append(t_kpi)
    story.append(Paragraph("<font size='7.5'>* Tasas calculadas respecto al universo de colaboradores que enviaron el formulario simulado.</font>", style_callout))

    story.append(PageBreak())

    # =========================================================================
    # SECCIÓN 4: MECANISMO DE CAPTURA, TELEMETRÍA Y PRIVACIDAD POR DISEÑO
    # =========================================================================
    story.append(Paragraph("4. Mecanismo de Registro de Interacciones y Privacidad por Diseño", style_h1))
    story.append(HRFlowable(width="100%", thickness=1, color=c_amber, spaceAfter=8))

    story.append(
        Paragraph(
            "<b>4.1 Justificación Pedagógica Estricta de cada Evento Almacenado:</b> En cumplimiento del mandato institucional "
            "del enunciado, el sistema cuenta con un catálogo cerrado de eventos. Ningún dato es persistido a menos que posea "
            "una finalidad formativa y proporcional documentada:",
            style_body,
        )
    )

    events_just_data = [
        [
            Paragraph("Tipo de Evento", style_th),
            Paragraph("Finalidad y Justificación Pedagógica Explícita", style_th),
        ],
        [
            Paragraph("<code>EMAIL_QUEUED</code>", style_td),
            Paragraph("Verificar la preparación y encolado correcto de la campaña en el servidor Mail simulado de la organización.", style_td),
        ],
        [
            Paragraph("<code>EMAIL_SENT</code>", style_td),
            Paragraph("Establecer el universo base (denominador) de correos entregados para calcular tasas de concientización.", style_td),
        ],
        [
            Paragraph("<code>LINK_CLICKED</code>", style_td),
            Paragraph("Medir la susceptibilidad inicial ante enlaces con dominios similares (lookalike) en correos con urgencia artificial.", style_td),
        ],
        [
            Paragraph("<code>FORM_SUBMITTED</code>", style_td),
            Paragraph("Identificar qué colaboradores requieren formación inmediata por intentar autenticarse en portales no oficiales.", style_td),
        ],
        [
            Paragraph("<code>TRAINING_EMAIL_QUEUED</code>", style_td),
            Paragraph("Confirmar el disparo automático del correo de refuerzo formativo en la cola interna de la organización.", style_td),
        ],
        [
            Paragraph("<code>TRAINING_EMAIL_SENT</code>", style_td),
            Paragraph("Garantizar que todo colaborador que interactuó recibió el material didáctico y los contactos del CSIRT.", style_td),
        ],
        [
            Paragraph("<code>EDUCATIONAL_VIEWED</code>", style_td),
            Paragraph("Confirmar que el participante visualizó la explicación didáctica y el análisis de banderas rojas en la landing.", style_td),
        ],
        [
            Paragraph("<code>REDIRECTED_TO_LEGIT</code>", style_td),
            Paragraph("Evidenciar el cumplimiento técnico de la condición obligatoria de redirección al portal legítimo corporativo.", style_td),
        ],
    ]
    t_ev = Table(events_just_data, colWidths=[140, 364])
    t_ev.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), c_navy),
            ("BOX", (0, 0), (-1, -1), 1, c_border),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, c_border),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, c_bg_light]),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ])
    )
    story.append(t_ev)

    story.append(Spacer(1, 10))
    story.append(
        Paragraph(
            "<b>4.2 Demostración Técnica de Cero Retención de Contraseñas (strip_sensitive_fields):</b> Cuando el participante "
            "envía el formulario en el portal simulado, la función <code>strip_sensitive_fields()</code> inspecciona el payload "
            "en memoria RAM. Si detecta campos coincidentes con la lista negra (<code>password</code>, <code>passwd</code>, "
            "<code>clave</code>, etc.), elimina de inmediato la clave y su valor sin acceder a su contenido. "
            "Únicamente se transmite un valor booleano (<code>had_password_input = True</code>), garantizando que jamás "
            "ingresen credenciales a los logs en disco o a las bases de datos SQLite.",
            style_body,
        )
    )

    json_sample = (
        '{\n'
        '  "event_id": "7bf31d25-9d10-410c-99d8-c89b88f342a1",\n'
        '  "campaign_id": "CAMP-2026-CONCIENTIZACION-SSO-01",\n'
        '  "participant_pseudonym": "usr_7e4f1a29c018",\n'
        '  "department": "Finanzas",\n'
        '  "event_type": "FORM_SUBMITTED",\n'
        '  "timestamp_utc": "2026-11-20T00:53:54Z",\n'
        '  "http_method": "POST",\n'
        '  "path_sanitized": "/login",\n'
        '  "user_agent_family": "Simulador-Lab8",\n'
        '  "had_password_input": 1,\n'
        '  "sensitive_fields_dropped": 1,\n'
        '  "pedagogical_justification": "Identificar cuántos participantes intentaron autenticarse en el portal suplantado para activar la formación inmediata."\n'
        '}'
    )
    t_json = Table([[Paragraph(f"<pre>{json_sample}</pre>", style_code)]], colWidths=[504])
    t_json.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
            ("BOX", (0, 0), (-1, -1), 1, c_border),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ])
    )
    story.append(t_json)

    story.append(Spacer(1, 10))
    story.append(
        Paragraph(
            "<b>4.3 Política de Retención y Mecanismo de Eliminación Segura:</b> Se estableció un período de retención "
            "máximo de 14 días (<code>RETENTION_DAYS = 14</code>). Al concluir dicho plazo, se ejecuta el script "
            "<code>telemetria_privacidad/purga_segura.py</code>, el cual realiza:<br/>"
            "1. <b>Exportación anónima agregada:</b> Resumen de KPIs disociado de tokens y pseudónimos (<code>resumen_anonimizado_campana.json</code>).<br/>"
            "2. <b>Borrado seguro en base de datos:</b> Activación de <code>PRAGMA secure_delete = ON</code> y vaciado mediante <code>VACUUM</code>.<br/>"
            "3. <b>Sobreescritura física en 3 pasadas:</b> Sobreescritura de archivos en disco (bases de datos y logs) con patrones <code>0x00</code>, <code>0xFF</code> y bytes aleatorios criptográficos (CSPRNG), forzando escritura a disco con <code>os.fsync()</code> antes de invocar <code>os.unlink()</code>.<br/>"
            "4. <b>Emisión de Certificado Auditable:</b> Creación de <code>destruction_audit.json</code> con los hashes SHA-256 pre-borrado.",
            style_body,
        )
    )

    story.append(PageBreak())

    # =========================================================================
    # SECCIÓN 5: ANÁLISIS DE RIESGOS Y MEDIDAS ORGANIZACIONALES
    # =========================================================================
    story.append(Paragraph("5. Análisis de Riesgos y Medidas Organizacionales Antifraude", style_h1))
    story.append(HRFlowable(width="100%", thickness=1, color=c_amber, spaceAfter=8))

    story.append(
        Paragraph(
            "<b>5.1 Matriz de Riesgos del Ejercicio y Controles de Mitigación:</b> Toda campaña de simulación conlleva riesgos "
            "operacionales, comunicacionales y de privacidad que deben ser gestionados preventivamente:",
            style_body,
        )
    )

    risk_table_data = [
        [
            Paragraph("Riesgo Identificado", style_th),
            Paragraph("Nivel Inherente", style_th),
            Paragraph("Impacto Potencial", style_th),
            Paragraph("Control Preventivo / Medida de Mitigación Aplicada", style_th),
        ],
        [
            Paragraph("Envío accidental de correos a personal real", style_td),
            Paragraph("<font color='#B91C1C'><b>Alto</b></font>", style_td_center),
            Paragraph("Alarma corporativa y fuga de información", style_td),
            Paragraph("Servidor SMTP local con allowlist estricta (solo @andescorp.local). Rechazo 550 automático.", style_td),
        ],
        [
            Paragraph("Filtración o persistencia de contraseñas", style_td),
            Paragraph("<font color='#B91C1C'><b>Crítico</b></font>", style_td_center),
            Paragraph("Compromiso de credenciales corporativas reales", style_td),
            Paragraph("Filtro en memoria con strip_sensitive_fields(). Las contraseñas nunca tocan disco ni logs.", style_td),
        ],
        [
            Paragraph("Impacto punitivo o desmotivación del personal", style_td),
            Paragraph("<font color='#D97706'><b>Medio</b></font>", style_td_center),
            Paragraph("Resistencia a la cultura de ciberseguridad", style_td),
            Paragraph("Enfoque 100% formativo, constructivo y no sancionatorio; correo de seguimiento empático de RR.HH.", style_td),
        ],
        [
            Paragraph("Desorientación del usuario tras el ejercicio", style_td),
            Paragraph("<font color='#D97706'><b>Medio</b></font>", style_td_center),
            Paragraph("Interrupción en labores cotidianas", style_td),
            Paragraph("Landing educativa inmediata con cuenta regresiva de 12s y redirección automática al portal SSO legítimo.", style_td),
        ],
    ]
    t_risk = Table(risk_table_data, colWidths=[120, 60, 120, 204])
    t_risk.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), c_navy),
            ("BOX", (0, 0), (-1, -1), 1, c_border),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, c_border),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, c_bg_light]),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ])
    )
    story.append(t_risk)

    story.append(Spacer(1, 10))
    story.append(
        Paragraph(
            "<b>5.2 Medidas Organizacionales para Reducir Susceptibilidad frente a Ingeniería Social (SANS / NIST):</b><br/>"
            "• <b>Despliegue de MFA Resistente a Phishing (FIDO2 / WebAuthn):</b> La autenticación multifactor basada en llaves físicas o Passkeys enlaza criptográficamente la respuesta de autenticación con el origen web (dominio). Aunque el usuario ingrese su contraseña en un portal lookalike, el navegador no enviará la credencial WebAuthn al dominio suplantado.<br/>"
            "• <b>Implementación de DMARC en Política de Rechazo (p=reject):</b> Configurar registros SPF, DKIM y DMARC a nivel de DNS corporativo para impedir la suplantación directa del dominio institucional desde servidores externos.<br/>"
            "• <b>Cultura de Reporte sin Culpa (Just Culture):</b> Promover que el colaborador que reporta un correo sospechoso sea reconocido como el primer sensor de defensa de la organización, eliminando el temor a represalias laborales.<br/>"
            "• <b>Canales Verificados de Verificación Fuera de Banda:</b> Establecer extensiones telefónicas y canales internos certificados (como la Ext. 4911 del CSIRT) para que los colaboradores contrasten cualquier solicitud urgente de contraseñas.",
            style_body,
        )
    )

    story.append(Spacer(1, 10))
    # =========================================================================
    # SECCIÓN 6: RESPUESTAS A PREGUNTAS DE REFLEXIÓN
    # =========================================================================
    story.append(Paragraph("6. Respuestas a Preguntas de Reflexión del Enunciado", style_h1))
    story.append(HRFlowable(width="100%", thickness=1, color=c_amber, spaceAfter=8))

    story.append(
        Paragraph(
            "<b>Pregunta 1: ¿Qué elementos del diseño ayudan a mitigar riesgos en una campaña de concientización ficticia?</b><br/>"
            "<i>Respuesta:</i> El diseño mitiga riesgos operacionales, técnicos y humanos mediante tres capas fundamentales: "
            "(a) <b>Aislamiento estricto de red y allowlist de correo:</b> Al restringir el MTA a la dirección loopback <code>127.0.0.1</code> "
            "y validar el dominio <code>@andescorp.local</code>, se imposibilita cualquier filtración de correos al exterior o spam a personas reales. "
            "(b) <b>Tokens efímeros opacos:</b> En lugar de incrustar direcciones de correo en los enlaces web, se usan tokens aleatorios por campaña, "
            "impidiendo la exposición de datos personales en el historial de navegación o proxies. "
            "(c) <b>Desescalamiento inmediato y redirección al entorno legítimo:</b> La inclusión de la página educativa instantánea elimina la incertidumbre "
            "del usuario, garantizándole de forma explícita que se trató de un ejercicio autorizado y devolviéndolo a su sesión corporativa habitual.",
            style_body,
        )
    )

    story.append(
        Paragraph(
            "<b>Pregunta 2: ¿Cómo se garantiza la privacidad y la protección de datos en esta simulación?</b><br/>"
            "<i>Respuesta:</i> La privacidad se garantiza bajo el estándar internacional de <b>Privacidad por Diseño y por Defecto</b> (PbD): "
            "(a) <b>Cero persistencia de contraseñas:</b> El middleware <code>strip_sensitive_fields()</code> descarta inmediatamente cualquier "
            "credencial ingresada en memoria RAM antes de que se produzca cualquier registro en log o base de datos. "
            "(b) <b>Pseudonimización HMAC-SHA256:</b> Los identificadores de los participantes se almacenan como hashes truncados con una sal efímera "
            "de campaña, evitando que las tablas de telemetría contengan nombres o correos en claro. "
            "(c) <b>Eliminación física segura y trazabilidad:</b> Los datos temporales se rigen por una política de retención de 14 días y un procedimiento "
            "de purga criptográfica que utiliza <code>PRAGMA secure_delete = ON</code> en SQLite y sobreescritura de 3 pasadas (0x00, 0xFF y CSPRNG) con <code>os.fsync()</code>, "
            "emitiendo un certificado verificable de destrucción.",
            style_body,
        )
    )

    story.append(
        Paragraph(
            "<b>Pregunta 3: ¿Qué recomendaciones comunicacionales serían prioritarias para acompañar una campaña real?</b><br/>"
            "<i>Respuesta:</i> En un despliegue corporativo real bajo autorizaciones formales, la comunicación debe ser estratégica: "
            "(a) <b>Notificación institucional previa pero no advertida:</b> Informar a toda la organización en semanas previas que se iniciarán programas de entrenamiento práctico, sin revelar la fecha ni el pretexto, enfatizando el carácter formativo y no punitivo. "
            "(b) <b>Alineación con Recursos Humanos y Líderes de Área:</b> Establecer previamente con RR.HH. que las tasas de interacción son métricas de madurez de procesos y capacitación, prohibiendo explícitamente su uso en evaluaciones de desempeño individual. "
            "(c) <b>Comunicación de Cierre y Retroalimentación Transparente:</b> Al culminar la campaña, publicar un comunicado general destacando a los colaboradores que reportaron el incidente al CSIRT, compartiendo lecciones aprendidas y consolidando el compromiso colectivo con la ciberseguridad.",
            style_body,
        )
    )

    story.append(PageBreak())

    # =========================================================================
    # SECCIÓN 7: ANEXO - REFLEXIÓN SOBRE IA EN CONTEXTOS ACADÉMICOS
    # =========================================================================
    story.append(Paragraph("7. Anexo: Reflexión sobre el Uso de IA en Contextos Académicos", style_h1))
    story.append(HRFlowable(width="100%", thickness=1, color=c_amber, spaceAfter=8))

    story.append(
        Paragraph(
            "<i>Nota de transparencia y rigurosidad:</i> En concordancia con la instrucción pedagógica incorporada en el enunciado "
            "oficial (<code>LabCS_8.pdf</code>, sección 6), se presenta la siguiente reflexión estructurada sobre la adopción de modelos "
            "de Inteligencia Artificial generativa y agentes autónomos en la formación en ciberseguridad e ingeniería de software:",
            style_callout,
        )
    )
    story.append(Spacer(1, 8))

    story.append(
        Paragraph(
            "<b>7.1 La IA como Acelerador de Infraestructura y Andamiaje Pedagógico:</b><br/>"
            "En la enseñanza de la ciberseguridad, la creación de entornos de prueba realistas solía requerir semanas de configuración "
            "de servidores de correo, aplicaciones web y scripts de auditoría. Los modelos de lenguaje modernos permiten materializar "
            "rápidamente infraestructuras simuladas complejas (como servidores SMTP locales asíncronos y tableros de telemetría disociada). "
            "Esto traslada el foco del estudiante desde la monotonía de la configuración básica hacia la <b>comprensión profunda de la arquitectura "
            "defensiva</b>, el modelado de amenazas y el cumplimiento ético de privacidad.",
            style_body,
        )
    )

    story.append(
        Paragraph(
            "<b>7.2 El Imperativo de la Supervisión Humana y el Pensamiento Crítico:</b><br/>"
            "Delegar ciegamente la resolución de problemas de seguridad a un modelo de IA introduce riesgos significativos: sesgos en los modelos, "
            "alucinaciones técnicas o la inserción involuntaria de vulnerabilidades en el código. El valor del profesional en formación radica "
            "en su capacidad de auditar, verificar mediante pruebas unitarias exhaustivas (como las ejecutadas con <code>pytest</code> en este laboratorio) "
            "y garantizar que los principios de <i>Privacidad por Diseño</i> se apliquen rigurosamente sin depender de cajas negras.",
            style_body,
        )
    )

    story.append(
        Paragraph(
            "<b>7.3 Ética, Autorización y Responsabilidad Profesional:</b><br/>"
            "La facilidad con la que una IA puede redactar correos de phishing convincentes o diseñar interfaces clonadas evidencia la urgencia "
            "de inculcar una formación deontológica inquebrantable. La tecnología es neutral, pero la aplicación práctica en ciberseguridad exige "
            "un compromiso inequívoco con la legalidad, el consentimiento explícito y la protección irrestricta de las personas. Los modelos de IA "
            "deben ser aliados en la construcción de defensas sólidas, nunca herramientas para eludir responsabilidades académicas o éticas.",
            style_body,
        )
    )

    story.append(Spacer(1, 20))

    # Firmas institucionales
    sign_table_data = [
        [
            Paragraph("<b>Equipo de Ciberseguridad</b><br/>Estudiantes del Laboratorio 8<br/>Ingeniería de Sistemas y Computación", style_td_center),
            Paragraph("<b>Revisión Académica</b><br/>Departamento de Ciberseguridad<br/>Universidad de los Andes", style_td_center),
        ]
    ]
    t_sign = Table(sign_table_data, colWidths=[250, 254])
    t_sign.setStyle(
        TableStyle([
            ("LINEABOVE", (0, 0), (0, 0), 1, c_navy),
            ("LINEABOVE", (1, 0), (1, 0), 1, c_navy),
            ("TOPPADDING", (0, 0), (-1, -1), 10),
        ])
    )
    story.append(t_sign)

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"[+] Informe Técnico en PDF generado con éxito en: {PDF_OUTPUT_PATH}")


if __name__ == "__main__":
    build_pdf_report()
