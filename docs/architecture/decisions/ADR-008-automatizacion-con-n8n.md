# ADR-008: Automatización de Avisos con n8n

## Estado
Aceptada — 2026-11-03

## Contexto
El punto (6) de la evaluación exige incorporar una capa de automatización de procesos sobre la aplicación de citas médicas ("La tormenta de avisos"). 

En las versiones anteriores, los avisos salían acoplados directamente al código del caso de uso mediante llamadas a Twilio o bitácoras en consola. Esto genera problemas de resiliencia:
- Si el canal de mensajería falla o se satura, bloquea o ralentiza la experiencia de usuario.
- No hay reintentos configurables ni flujos complejos (por ejemplo, escalar a correo si el WhatsApp falla, o avisos diferenciados por estado de cita).
- No permite a analistas u operadores modificar los canales de aviso sin alterar el código fuente del backend.

## Decisión
1. **Adición de n8n al stack de Docker Compose**: Se incorpora un servicio `n8n` corriendo en el puerto `5678` conectado a la red interna de Docker.
2. **Adaptador `N8nWebhookSender`**: Implementa el puerto de dominio `NotificationSender`. Cuando ocurre un evento de agendado, confirmación, reagendado o cancelación, el backend despacha un payload JSON asíncrono/desacoplado al webhook de n8n (`http://n8n:5678/webhook/medical-appointment-notifications`).
3. **Resiliencia (ADR-004)**: Siguiendo la regla de no-bloqueo, cualquier timeout o caída de n8n nunca revierte la transacción de la base de datos de la cita médica; simplemente se registra la anomalía en bitácora.
4. **Orquestación visual en n8n**: En n8n se recibe el webhook, se clasifica el tipo de evento (`CITA_NUEVA`, `CITA_CONFIRMADA`, `CITA_CANCELADA`) y se encamina el aviso correspondiente.

## Consecuencias
- **Punto 6 del curso cubierto al 100%**: Se demuestra automatización real basada en eventos mediante herramientas de integración low-code (n8n).
- **Desacoplamiento total**: El backend no sabe cómo se envía el mensaje (WhatsApp, correo, Slack o Telegram); solo notifica el hecho a n8n.
