# Checklist de Buenas Prácticas Anti-Phishing — AndesCorp S.A.

> **Uso previsto:** Material de concientización listo para distribución por Recursos Humanos y Seguridad de la Información (alineado con guías **NIST SP 800-50** y **SANS Security Awareness**).

## Antes de abrir enlaces o adjuntos en un correo

- [ ] **Verificar el dominio exacto del remitente:** Confirmar que la dirección termine exactamente en `@andescorp.local` y no en variaciones engañosas (*lookalike*) como `@andescorp-ti.local` o `@andesc0rp.local`.
- [ ] **Evaluar el tono de urgencia:** Desconfiar de mensajes que exigen acción inmediata, amenazan con bloqueos de cuenta o prometen beneficios urgentes.
- [ ] **Inspeccionar el enlace real:** Pasar el puntero sobre el botón o enlace para verificar el destino antes de hacer clic.
- [ ] **No usar enlaces del correo para iniciar sesión:** Abrir una pestaña nueva y entrar al portal corporativo oficial (`sso.andescorp.local`) mediante marcadores guardados.
- [ ] **Revisar la barra de direcciones completa:** Un portal *evil-twin* puede replicar el diseño visual y el logotipo corporativo, pero el nombre de dominio en la barra de direcciones lo delata.
- [ ] **Apoyarse en el gestor de contraseñas:** Los gestores legítimos no autocompletan credenciales en dominios falsos aunque se vean idénticos.
- [ ] **Validar por un canal alterno:** Si un correo de TI, RR.HH. o Gerencia resulta inusual, confirmar mediante la intranet oficial o una llamada interna.

## Hábitos permanentes de protección

- [ ] Mantener habilitada la **autenticación multifactor (MFA)** resistente a phishing (llaves FIDO2/Passkeys o autenticador corporativo).
- [ ] Utilizar contraseñas únicas por servicio (nunca reutilizar la contraseña corporativa en sitios externos).
- [ ] Mantener el navegador y el sistema operativo actualizados para aprovechar filtros anti-phishing y parches de seguridad.
- [ ] Reportar cualquier correo sospechoso aunque no se haya hecho clic: un reporte temprano protege al resto de la organización.
