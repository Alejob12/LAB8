# Contenido Didáctico de la Página Educativa Inmediata (Landing Post-Interacción)

**Organización Ficticia:** AndesCorp S.A. (`andescorp.local`)  
**Campaña de Concientización:** `CAMP-2026-CONCIENTIZACION-SSO-01`  
**Destinatarios:** Colaboradores que interactuaron con el formulario de inicio de sesión simulado.

---

## 1. Encabezado de Desescalamiento y Tranquilidad

> **¡Alto! Acabas de interactuar con una simulación pedagógica autorizada.**  
> Este ejercicio forma parte del Programa Interno de Concientización en Ciberseguridad de AndesCorp S.A. y Recursos Humanos.  
> **Su propósito es 100% formativo, constructivo y no sancionatorio.**

### Garantía de Privacidad por Diseño (Cero Retención de Contraseñas)
- **Tu contraseña corporativa NO ha sido almacenada, transmitida ni expuesta.**
- El sistema de laboratorio descarta en memoria cualquier credencial sensible inmediatamente mediante filtros automáticos (`strip_sensitive_fields()`).
- Únicamente se registró un indicador estadístico anónimo para evaluar las necesidades de capacitación del equipo y activar este material didáctico.
- Se ha remitido a tu bandeja de correo un mensaje explicativo de RR.HH. con recursos adicionales.

---

## 2. Anatomía del Ataque: Las 4 Banderas Rojas de la Simulación

| # | Bandera Roja Diseñada | Detalle Observado en el Ejercicio | Indicador de Autenticidad Legítima |
|---|---|---|---|
| **1** | **Dominio Lookalike en el Remitente** | `soporte-verificacion@andescorp-ti.local` | El dominio oficial corporativo es únicamente `@andescorp.local`. El subdominio o sufijo `-ti` es un dominio suplantado. |
| **2** | **Urgencia Artificial y Amenaza** | "Plazo límite: Menos de 2 horas para evitar la suspensión temporal de su cuenta" | Los ciberdelincuentes crean sensación de pánico y prisa para forzar decisiones impulsivas sin verificar. |
| **3** | **URL del Portal Suplantado ("Evil-Twin")** | Enlace dirigido al puerto `8002` con host simulado `sso-andescorp-verificacion.local` | El portal Single Sign-On oficial legítimo opera en `sso.andescorp.local` (puerto `8001`) con certificado y URL corporativa conocida. |
| **4** | **Solicitud de Credenciales vía Enlace** | Formulario web solicitando contraseña tras pulsar un botón de correo | Las áreas de TI y Seguridad **nunca** solicitan renovar o validar contraseñas a través de enlaces directos recibidos por correo electrónico. |

---

## 3. Protocolo P.A.R.A. para Empleados

```
  [P] PAUSA    --> Detente 30 segundos ante cualquier mensaje que genere prisa o miedo.
  [A] ANALIZA  --> Revisa el remitente exacto (letra por letra) y pasa el cursor sobre la URL.
  [R] REPORTA  --> Reenvía correos sospechosos al CSIRT (csirt@andescorp.local / Ext. 4911).
  [A] APRENDE  --> Usa marcadores guardados oficiales, contraseñas únicas y verificación MFA.
```

---

## 4. Flujo de Redirección Automática al Entorno Legítimo

- La página educativa presenta un contador visual regresivo de **12 segundos** (`REDIRECT_COUNTDOWN_SECONDS`).
- Ofrece un botón de acción inmediata: **`Continuar al Portal Legítimo Ahora`**.
- Al cumplirse el tiempo o pulsar el botón, el usuario es redirigido mediante HTTP 302 a:  
  `http://127.0.0.1:8001/login?from_simulation=1`
- En el portal legítimo, un banner verde confirma la llegada segura al entorno oficial corporativo.

---

## 5. Recomendaciones Prácticas si se Sospecha de un Incidente Real

1. **No reenviar el correo a compañeros** para no propagar el riesgo.
2. **Reenviar el mensaje original con cabeceras completas** a `csirt@andescorp.local`.
3. **Si introdujo credenciales reales en un sitio no autorizado:**
   - Cambiar la contraseña inmediatamente desde el portal SSO legítimo oficial.
   - Contactar de inmediato a la Mesa de Ayuda / CSIRT (`Ext. 4911`) para invalidar sesiones activas y renovar tokens MFA.
