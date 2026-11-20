# Laboratorio 8 — Phishing y Evil Twin (Entorno Simulado)

**Universidad de los Andes · Ingeniería de Sistemas y Computación · Ciberseguridad**  
**Organización ficticia del laboratorio:** `AndesCorp S.A.` (`andescorp.local`)  
**Documento base:** `LabCS_8.pdf` (v1.1)  
**Estado del proyecto:** **100 % Implementado y Verificado**

> [!CAUTION]
> **Declaración de alcance y ética:** Todo este proyecto es **estrictamente ficticio, educativo y confinado a un entorno controlado de laboratorio** (`127.0.0.1` / dominio local `@andescorp.local`). No involucra personal real ni sistemas productivos, no envía correos externos y **jamás almacena contraseñas en texto claro**. Cumple con todas las restricciones éticas y normativas estipuladas en el enunciado `LabCS_8.pdf`.

---

## 1. Guía Rápida de Ejecución

El laboratorio cuenta con un entorno virtual Python (`.venv`) con todas las dependencias instaladas (`Flask`, `requests`, `pytest`, `pytest-asyncio`, `reportlab`, `Pillow`).

### 1.1 Ejecutar Suite de Pruebas Automatizadas
Verifica allowlist SMTP, cero almacenamiento de contraseñas, flujo e2e y purga segura en 3 pasadas:
```bash
./.venv/bin/pytest -v
```

### 1.2 Arrancar los 5 Servicios del Laboratorio
Inicia de forma orquestada los 5 servicios en segundo plano (`127.0.0.1`):
```bash
./.venv/bin/python run_lab.py start
```

| Servicio | Puerto | URL Local | Descripción |
|---|:---:|---|---|
| **Servidor SMTP Local** | `1025` | `127.0.0.1:1025` | MTA asíncrono RFC 5321 (rechazo 550 fuera de `@andescorp.local`) |
| **Portal SSO Legítimo** | `8001` | `http://127.0.0.1:8001/login` | Portal corporativo oficial (destino seguro post-redirección) |
| **Portal Evil-Twin** | `8002` | `http://127.0.0.1:8002/login` | Portal simulado (cero contraseñas + landing educativa) |
| **Webmail Corporativo** | `8025` | `http://127.0.0.1:8025/` | Bandeja institucional, visor de colas y logs SMTP en vivo |
| **Dashboard Telemetría** | `8003` | `http://127.0.0.1:8003/` | Tablero de KPIs y garantías de privacidad por diseño |

### 1.3 Despachar Campaña Simulación y Ejecutar Actividad
```bash
# 1. Despachar correo urgente a los 8 colaboradores ficticios
./.venv/bin/python run_lab.py send-campaign

# 2. Simular interacción realista (clics, envíos, correos de RR.HH. y redirecciones)
./.venv/bin/python run_lab.py simulate-activity

# 3. Consultar estado y salud de los servicios
./.venv/bin/python run_lab.py status
```

### 1.4 Compilar el Informe Técnico Oficial en PDF
Genera el documento final [Informe_Tecnico_Laboratorio_8.pdf](file:///Users/alejandrobernal/Desktop/LAB8/Informe_Tecnico_Laboratorio_8.pdf) con diagramas, tablas y reflexiones:
```bash
./.venv/bin/python generar_informe_pdf.py
```

### 1.5 Detener Servicios o Ejecutar Purga Criptográfica
```bash
# Detener servicios en segundo plano
./.venv/bin/python run_lab.py stop

# Ejecutar purga criptográfica con sobreescritura en 3 pasadas (0x00, 0xFF, CSPRNG)
./.venv/bin/python run_lab.py purge --confirm
```

---

## 2. Mapa Completo de Entregables del Proyecto

### Entregable 1: Informe Técnico en PDF
- **Archivo generado:** [Informe_Tecnico_Laboratorio_8.pdf](file:///Users/alejandrobernal/Desktop/LAB8/Informe_Tecnico_Laboratorio_8.pdf)
- **Contenido estructurado:**
  1. Portada institucional (UniAndes, Ciberseguridad, Lab 8) y declaración obligatoria de ética y alcance.
  2. Diseño de la simulación, alcance, población ficticia (8 participantes) y propósito pedagógico.
  3. Esquema arquitectural con **diagrama visual de flujo completo** ([evidencias/diagrama_flujo.png](file:///Users/alejandrobernal/Desktop/LAB8/evidencias/diagrama_flujo.png)) y plantilla del correo simulado.
  4. Evidencias de implementación en entorno controlado: tabla de servicios, log SMTP con rechazo 550 a correos externos y tabla de KPIs de concientización.
  5. Mecanismo de captura y telemetría: justificación pedagógica de cada evento, demostración técnica de no-retención de contraseñas (`strip_sensitive_fields`) y política de retención/eliminación segura.
  6. Análisis de riesgos, matriz de mitigación y medidas organizacionales (MFA FIDO2, DMARC `p=reject`, cultura sin culpa).
  7. Respuestas exhaustivas a las tres preguntas de reflexión del enunciado.
  8. Anexo formal: Reflexión sobre el uso de modelos de Inteligencia Artificial en contextos académicos y de ciberseguridad.

### Entregable 2: Paquete de Materiales de Formación (RR.HH. y Educación)
Todos los materiales están organizados y listos para distribución en [materiales_formacion/](file:///Users/alejandrobernal/Desktop/LAB8/materiales_formacion/):
1. **Correo de Seguimiento de RR.HH.:**
   - [correo-seguimiento-rrhh.html](file:///Users/alejandrobernal/Desktop/LAB8/materiales_formacion/correo-seguimiento-rrhh.html) (versión responsive corporativa)
   - [correo-seguimiento-rrhh.txt](file:///Users/alejandrobernal/Desktop/LAB8/materiales_formacion/correo-seguimiento-rrhh.txt) (versión texto plano)
2. **Infografía y Checklist Anti-Phishing:**
   - [infografia-antiphishing.svg](file:///Users/alejandrobernal/Desktop/LAB8/materiales_formacion/infografia-antiphishing.svg) (diseño vectorial de alta definición)
   - [infografia-antiphishing.html](file:///Users/alejandrobernal/Desktop/LAB8/materiales_formacion/infografia-antiphishing.html) (visor interactivo imprimible a PDF)
   - [checklist-buenas-practicas.md](file:///Users/alejandrobernal/Desktop/LAB8/materiales_formacion/checklist-buenas-practicas.md) (guía alineada a NIST SP 800-50 y SANS)
3. **Guía de Reporte de Incidentes y Contenido Educativo:**
   - [guia-reporte-incidentes.md](file:///Users/alejandrobernal/Desktop/LAB8/materiales_formacion/guia-reporte-incidentes.md) (protocolo CSIRT en 3 escenarios)
   - [contenido-pagina-educativa.md](file:///Users/alejandrobernal/Desktop/LAB8/materiales_formacion/contenido-pagina-educativa.md) (contenido didáctico post-interacción y desescalamiento)

---

## 3. Estado Detallado de Implementación por Criterio de Evaluación

| Criterio de Evaluación | Ponderación | Estado | Evidencia y Módulos Clave |
|---|:---:|:---:|---|
| **Evidencia de implementación del "evil-twin" en entorno simulado** | **30 %** |  **100 %** | Módulo [portal_evil_twin/](file:///Users/alejandrobernal/Desktop/LAB8/portal_evil_twin/), host simulado `sso-andescorp-verificacion.local:8002`, página educativa inmediata, cuenta regresiva y redirección segura HTTP 302 a `portal_legitimo/login?from_simulation=1`. |
| **Evidencia de preparación y envío de correos en entorno simulado** | **30 %** |  **100 %** | Módulo [campana_correo/](file:///Users/alejandrobernal/Desktop/LAB8/campana_correo/), servidor [servidor_correo/smtp_local.py](file:///Users/alejandrobernal/Desktop/LAB8/servidor_correo/smtp_local.py), cola trazable `MailQueueService`, allowlist estricta y [Webmail corporativo](file:///Users/alejandrobernal/Desktop/LAB8/servidor_correo/webmail_app.py) con visor de buzones y colas. |
| **Mecanismo de captura, telemetría y eliminación segura** | **30 %** |  **100 %** | Módulo [telemetria_privacidad/](file:///Users/alejandrobernal/Desktop/LAB8/telemetria_privacidad/), filtro `strip_sensitive_fields()` (cero contraseñas), pseudonimización HMAC-SHA256, [dashboard web](file:///Users/alejandrobernal/Desktop/LAB8/telemetria_privacidad/dashboard_app.py), purga segura en 3 pasadas y certificado `destruction_audit.json`. |
| **Calidad de materiales de formación y flujo de redirección** | **10 %** |  **100 %** | Módulo [materiales_formacion/](file:///Users/alejandrobernal/Desktop/LAB8/materiales_formacion/), correo RR.HH., infografía SVG, checklist NIST/SANS, guía de reporte CSIRT y contenido de la página educativa. |
| **Total Académico** | **100 %** |  **Cumplimiento Total** | Código, pruebas unitarias automatizadas (`pytest`), evidencias y PDF oficial completados. |

---

## 4. Estructura de Directorios del Repositorio

```text
.
├── LabCS_8.pdf                          # Enunciado oficial del laboratorio
├── Informe_Tecnico_Laboratorio_8.pdf    # Entregable 1: Informe técnico en PDF compilado
├── README.md                            # Documentación y manual integral
├── requirements.txt                     # Dependencias de Python
├── pytest.ini                           # Configuración de pruebas automatizadas
├── run_lab.py                           # Orquestador CLI de servicios y simulaciones
├── generar_informe_pdf.py               # Generador del informe en PDF con ReportLab
├── generar_evidencias_y_diagrama.py     # Extractor de evidencias y generador del diagrama
├── config/                              # Configuración centralizada
│   ├── settings.py                      # Parámetros de red, puertos, retención y dominios
│   └── usuarios_ficticios.json          # 8 colaboradores ficticios de AndesCorp S.A.
├── campana_correo/                      # Despacho de campaña simulada
│   ├── despachador.py                   # Encolado y envío hacia SMTP local
│   └── plantillas/                      # Plantillas HTML y texto del correo simulado
├── portal_legitimo/                     # Portal corporativo SSO legítimo (:8001)
│   ├── app.py                           # Servicio Flask y entrega de materiales
│   └── templates/                       # Plantillas login y panel corporativo
├── portal_evil_twin/                    # Portal simulado "Evil-Twin" (:8002)
│   ├── app.py                           # Servidor Flask, filtro de credenciales y redirección
│   └── templates/                       # Login lookalike y landing educativa
├── servidor_correo/                     # Servidor de correo interno y Webmail (:1025 / :8025)
│   ├── smtp_local.py                    # Servidor SMTP asíncrono con allowlist estricta
│   ├── mail_queue.py                    # Gestor de cola con trazabilidad
│   ├── mail_storage.py                  # Persistencia SQLite (PRAGMA secure_delete = ON)
│   ├── webmail_app.py                   # Interfaz Webmail corporativa
│   └── templates/                       # Visor de correos, colas y logs SMTP
├── telemetria_privacidad/               # Telemetría pedagógica y Privacidad por Diseño
│   ├── sanitizer.py                     # Cero contraseñas y pseudonimización HMAC
│   ├── storage.py                       # TelemetryStore en SQLite y logs JSONL
│   ├── purga_segura.py                  # Sobreescritura en 3 pasadas y certificado audit
│   ├── dashboard_app.py                 # Tablero web de concientización (:8003)
│   └── templates/                       # Vista del dashboard de métricas
├── materiales_formacion/                # Entregable 2: Paquete formativo para RR.HH.
│   ├── correo-seguimiento-rrhh.html     # Correo de refuerzo en HTML
│   ├── correo-seguimiento-rrhh.txt      # Correo de refuerzo en texto plano
│   ├── infografia-antiphishing.svg      # Infografía visual vectorial
│   ├── infografia-antiphishing.html     # Visor HTML imprimible de la infografía
│   ├── checklist-buenas-practicas.md    # Checklist anti-phishing (NIST / SANS)
│   ├── guia-reporte-incidentes.md       # Guía de reporte ante incidentes reales CSIRT
│   └── contenido-pagina-educativa.md    # Contenido de la página educativa inmediata
├── evidencias/                          # Artefactos extraídos de la ejecución real
│   ├── diagrama_flujo.png               # Diagrama esquemático en alta definición
│   ├── resumen_metricas.json            # KPIs consolidados de la campaña
│   ├── extracto_interactions.jsonl      # Ejemplo real de eventos sanitizados
│   ├── extracto_smtp_server.log         # Ejemplo real de logs SMTP
│   └── extracto_mail_queue.jsonl        # Ejemplo real de transiciones de cola
└── tests/                               # Suite de pruebas automatizadas con pytest
    ├── test_smtp_allowlist.py           # Validación de rechazo 550 fuera de allowlist
    ├── test_privacy_zero_passwords.py   # Demostración de cero retención de contraseñas
    ├── test_end_to_end_flow.py          # Flujo e2e (correo -> click -> submit -> redir)
    └── test_secure_purge.py             # Verificación de sobreescritura y certificado
```
