# ADR-005: Modelar las transiciones de estado como subrecursos

## Estado
Aceptada — 2026-09-22

## Contexto

El sistema anterior expone `POST /admin/appointments/{id}/move-to-24hours`. La guia
AIVARA es explicita: **usar sustantivos, no verbos** en las URI, y da como ejemplo a
evitar precisamente formas como `getOrdersByCustomer`.

Las citas tienen transiciones —confirmar, atender, cancelar— que no encajan
comodamente en un `PUT` sobre el recurso completo.

## Decision

Modelar cada transicion como un **subrecurso sustantivado** con `PUT`:

| Operacion | Endpoint |
|---|---|
| Confirmar | `PUT /api/v1/appointments/{id}/confirmation` |
| Marcar atendida | `PUT /api/v1/appointments/{id}/completion` |
| Cancelar | `PUT /api/v1/appointments/{id}/cancellation` |
| Reagendar | `PATCH /api/v1/appointments/{id}` |

`move-to-24hours` **desaparece**: mover una cita al dia siguiente es un `PATCH` con
la fecha nueva. La logica sigue disponible como `move_to_next_day()` en el caso de
uso, para el cron y para futuros atajos de la interfaz.

Las respuestas incluyen `_links` para auto-descubrimiento, como sugiere la guia.

## Consecuencias

**Positivas**

- Ninguna URI contiene un verbo.
- `PUT` sobre el subrecurso es **idempotente** en el sentido util: reconfirmar algo
  ya confirmado devuelve 409 con un mensaje claro en lugar de duplicar efectos.
- La revalidacion de conflictos ahora **si** ocurre al mover una cita; el endpoint
  original la omitia.

**Negativas**

- `PUT /appointments/1/cancellation` es menos obvio a primera vista que
  `POST /appointments/1/cancel` para quien no conoce la convencion.
- Un subrecurso por transicion hace crecer la superficie de la API.

## Alternativas consideradas

- **`PATCH` con `{"status": 4}`**: deja que el cliente elija cualquier transicion,
  incluidas las ilegales, y obliga al servidor a inferir la intencion.
- **`POST /appointments/{id}/actions` con el verbo en el cuerpo**: esconde el verbo
  en el payload, respetando la letra de la regla pero no su proposito.
