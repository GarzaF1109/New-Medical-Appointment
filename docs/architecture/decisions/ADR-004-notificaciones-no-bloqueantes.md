# ADR-004: Las notificaciones fallidas no revierten operaciones de negocio

## Estado
Aceptada — 2026-09-22

## Contexto

Al agendar una cita ocurren dos cosas: se guarda un registro y se avisa al paciente
por WhatsApp. La segunda depende de un tercero (Twilio) que puede estar caido, ser
lento o rechazar el mensaje.

La pregunta es qué hacer si el guardado tiene exito y la notificacion falla.

## Decision

La cita **se conserva**. `NotificationSender.send()` devuelve un booleano y **nunca
lanza excepcion**: el adaptador de Twilio absorbe errores de red y respuestas de
error, los registra en bitacora y devuelve `False`.

El resultado del caso de uso incluye `notification_sent`, que la API expone como
`notificationSent` para que la interfaz informe al usuario con precision.

Ademas, un paciente **sin telefono registrado** es un caso valido de negocio, no un
error: `notification_sent` vale `False` y la cita se agenda igual.

## Consecuencias

**Positivas**

- Una caida de Twilio no impide operar la clinica.
- La recepcionista ve exactamente qué paso y puede llamar por telefono si hizo falta.
- Los casos de uso se prueban con un `SpyNotificationSender` que simula ambos
  desenlaces sin tocar la red.

**Negativas**

- Puede quedar una cita agendada de la que el paciente nunca se entero. Se mitiga
  informando en la interfaz y con el recordatorio automatico de 24 horas.
- No hay reintento automatico. Si se vuelve un problema real, la evolucion natural
  es una cola de mensajes con reintentos; el puerto `NotificationSender` ya permite
  introducirla sin tocar el dominio.

## Alternativas consideradas

- **Transaccion atomica (revertir la cita si falla el aviso)**: perder la cita del
  paciente por un problema de un proveedor externo es un peor resultado de negocio.
- **Lanzar la excepcion al cliente HTTP**: devolveria un 500 sobre una operacion que
  en realidad tuvo exito, confundiendo al usuario.
