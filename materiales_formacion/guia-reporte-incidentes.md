# Guía Corta: ¿Qué hacer si sospechas de un incidente de Phishing REAL?

**Organización ficticia:** AndesCorp S.A. (`andescorp.local`)  
**Canal de respuesta a incidentes (CSIRT):** `csirt@andescorp.local` · **Ext. 4911** (24/7)

---

## Caso 1: Recibiste un correo sospechoso, pero NO hiciste clic

1. **No respondas** al remitente ni intentes "darse de baja" en enlaces internos del correo.
2. **No descargues ni abras** archivos adjuntos.
3. **Reporta el correo** reenviándolo (idealmente como archivo adjunto `.eml` para conservar cabeceras) a `csirt@andescorp.local` con el asunto `[REPORTE PHISHING]`.
4. **Elimínalo** de tu bandeja una vez confirmado el reporte.

## Caso 2: Hiciste clic en un enlace, pero NO ingresaste datos

1. **Cierra inmediatamente la pestaña** del navegador sin interactuar con ningún botón ni aceptar descargas.
2. **Notifica al CSIRT** (`csirt@andescorp.local` / Ext. 4911) indicando la hora aproximada y la URL visitada para que TI bloquee el dominio en el proxy/DNS corporativo.
3. Si se descargó algún archivo involuntariamente, **no lo ejecutes** e infórmalo al CSIRT para revisión del equipo.

## Caso 3: Ingresaste tu contraseña o un código MFA en un sitio sospechoso

> **Actúa rápido y sin temor:** Reportar a tiempo reduce drásticamente el impacto. En AndesCorp S.A. el reporte oportuno nunca se penaliza.

1. **Cambia tu contraseña de inmediato** accediendo directamente al portal SSO legítimo (`sso.andescorp.local`) desde un marcador oficial.
2. Si utilizabas esa misma contraseña en otros sistemas, **cámbiala también allí**.
3. **Llama de inmediato al CSIRT (Ext. 4911)** para que puedan:
   - Revocar todas las sesiones y tokens activos de tu cuenta.
   - Revisar accesos recientes e inicios de sesión inusuales.
   - Restablecer el factor MFA si fue comprometido.
4. **No borres el correo original ni el historial del navegador** hasta que el CSIRT tome evidencia para investigar el incidente.

---

*Material preparado para uso educativo y de RR.HH. — Laboratorio 8 de Ciberseguridad.*
