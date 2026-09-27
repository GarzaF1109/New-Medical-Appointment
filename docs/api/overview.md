# API REST — Vision general

**Base**: `/api/v1` · **Documentacion interactiva**: `http://localhost:8000/docs`
· **Especificacion**: `http://localhost:8000/openapi.json`

El documento OpenAPI lo **genera FastAPI** desde los esquemas Pydantic. No se
mantiene a mano, por lo que no puede desincronizarse de la implementacion.

## Convenciones

| Regla de la guia | Como se aplica |
|---|---|
| Sustantivos, no verbos | `/appointments`, nunca `/getAppointments` |
| Plural para colecciones | `/appointments`, `/patients`, `/doctors` |
| Jerarquia para lo relacionado | `/doctors/{id}/appointments` |
| Query params para filtrar | `?doctorId=1&status=2&dateFrom=2026-10-01` |
| Version en la ruta | `/api/v1/...` |
| camelCase en JSON | `startTime`, `patientName`, `notificationSent` |
| Auto-descubrimiento | Bloque `_links` en cada cita |

## Endpoints

### Citas

| Metodo | Ruta | Exito | Descripcion |
|---|---|---|---|
| `GET` | `/appointments` | 200 | Lista paginada y filtrable |
| `POST` | `/appointments` | 201 | Agenda una cita |
| `GET` | `/appointments/{id}` | 200 | Consulta una cita |
| `PATCH` | `/appointments/{id}` | 200 | Reagenda o reasigna |
| `PUT` | `/appointments/{id}/confirmation` | 200 | Confirma |
| `PUT` | `/appointments/{id}/completion` | 200 | Marca como atendida |
| `PUT` | `/appointments/{id}/cancellation` | 200 | Cancela |
| `DELETE` | `/appointments/{id}` | 204 | Elimina |

### Catalogos

| Metodo | Ruta | Descripcion |
|---|---|---|
| `GET` | `/patients` · `/patients/{id}` | Pacientes |
| `POST` | `/patients` | Registrar un paciente |
| `PATCH` | `/patients/{id}` | Editar un paciente (parcial) |
| `DELETE` | `/patients/{id}` | Eliminar un paciente |
| `GET` | `/patients/{id}/appointments` | Historial del paciente |
| `GET` | `/doctors` · `/doctors/{id}` | Doctores |
| `POST` | `/doctors` | Registrar un doctor |
| `PATCH` | `/doctors/{id}` | Editar un doctor (parcial) |
| `DELETE` | `/doctors/{id}` | Eliminar un doctor |
| `GET` | `/doctors/{id}/appointments` | Agenda del doctor |

### Edicion parcial de catalogos

`PATCH` solo toca los campos presentes en el cuerpo. La distincion entre "no
enviado" y "enviado como `null`" es significativa: omitir `phone` lo conserva,
mientras que enviar `"phone": null` deja al paciente sin telefono. Lo mismo
aplica a `medicalLicenseNumber` en doctores.

### Baja de catalogos

Un paciente o un doctor con citas **vigentes** -ni canceladas ni atendidas- no
puede eliminarse: la API responde `409 CONFLICT`. Primero hay que cancelar esas
citas, que es la accion que conserva la trazabilidad clinica. Al eliminar a la
persona, su historial de citas ya cerradas se borra en cascada.

### Operacion

| Metodo | Ruta | Descripcion |
|---|---|---|
| `GET` | `/health` | Sonda de salud (sin prefijo de version) |

## Codigos de estado

| Codigo | Cuando |
|---|---|
| `200` | Lectura o actualizacion correcta |
| `201` | Cita creada |
| `204` | Cita eliminada |
| `404` | La cita, el paciente o el doctor no existen |
| `409` | Conflicto de horario, o transicion ilegal desde el estado actual |
| `422` | Datos invalidos: motivo corto, fecha pasada, duracion fuera de rango |
| `500` | Error no controlado; el detalle va a la bitacora, nunca al cliente |

## Formato de error

Toda respuesta de error comparte la misma forma:

```json
{
  "status": 409,
  "code": "CONFLICT",
  "message": "El doctor ya tiene una cita en ese horario."
}
```

Los fallos de validacion agregan `details`:

```json
{
  "status": 422,
  "code": "VALIDATION_ERROR",
  "message": "Datos de entrada invalidos.",
  "details": [
    { "field": "reason", "message": "String should have at least 10 characters" }
  ]
}
```

## Ejemplos

Agendar:

```bash
curl -X POST http://localhost:8000/api/v1/appointments \
  -H 'Content-Type: application/json' \
  -d '{
    "patientId": 1,
    "doctorId": 1,
    "date": "2026-12-10",
    "startTime": "10:00:00",
    "durationMinutes": 60,
    "reason": "Dolor de cabeza persistente"
  }'
```

Respuesta `201`:

```json
{
  "id": 1,
  "patientId": 1,
  "patientName": "Ana Maria Lopez",
  "doctorId": 1,
  "doctorName": "Dr(a). Elena Navarro",
  "date": "2026-12-10",
  "startTime": "10:00:00",
  "endTime": "11:00:00",
  "durationMinutes": 60,
  "reason": "Dolor de cabeza persistente",
  "status": 1,
  "statusLabel": "Pendiente",
  "notificationSent": true,
  "_links": {
    "self":   { "href": "/api/v1/appointments/1" },
    "patient":{ "href": "/api/v1/patients/1" },
    "doctor": { "href": "/api/v1/doctors/1" },
    "cancel": { "href": "/api/v1/appointments/1/cancellation" }
  }
}
```

Reagendar y cancelar:

```bash
curl -X PATCH http://localhost:8000/api/v1/appointments/1 \
  -H 'Content-Type: application/json' -d '{"startTime": "15:00:00"}'

curl -X PUT http://localhost:8000/api/v1/appointments/1/cancellation
```

## Estados de una cita

| Valor | Etiqueta | Transiciones permitidas |
|---|---|---|
| `1` | Pendiente | → Confirmada, Completada, Cancelada |
| `2` | Confirmada | → Completada, Cancelada |
| `3` | Completada | ninguna (terminal) |
| `4` | Cancelada | ninguna (terminal); **libera el horario** |
