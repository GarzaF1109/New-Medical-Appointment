# C4 Nivel 2 — Contenedores

| Contenedor | Tecnologia | Responsabilidad | Puerto |
|---|---|---|---|
| **Frontend web** | React 19 + TypeScript + Vite, servido por Nginx | Interfaz de la recepcion; consume la API REST | 8080 |
| **API backend** | Python 3.12 + FastAPI + Uvicorn | Reglas de negocio y contrato REST versionado | 8000 |
| **Base de datos** | PostgreSQL 17 | Persistencia de citas, pacientes y doctores | 5432 |
| **Colector OTel** | OpenTelemetry Collector | Recepcion y reenvio de telemetria | 4317 |

## Diagrama

```mermaid
C4Container
    Person(recepcion, "Recepcionista")

    Container_Boundary(sistema, "Gestion de Citas Medicas") {
        Container(web, "Frontend web", "React + TypeScript + Nginx", "Formulario de agendado, tabla y filtros")
        Container(api, "API backend", "FastAPI + Python 3.12", "Casos de uso, dominio y contrato REST")
        ContainerDb(db, "Base de datos", "PostgreSQL 17", "Citas, pacientes, doctores")
    }

    System_Ext(twilio, "Twilio WhatsApp API")

    Rel(recepcion, web, "Usa", "HTTPS")
    Rel(web, api, "Consume", "JSON/HTTPS · /api/v1")
    Rel(api, db, "Lee y escribe", "SQL/psycopg")
    Rel(api, twilio, "Notifica", "HTTPS/REST")
```

## Decisiones de despliegue

- Nginx sirve el frontend **y** hace proxy de `/api/` hacia el backend, de modo que
  ambos comparten origen y CORS deja de ser un problema en produccion.
- En desarrollo, el proxy de Vite cumple el mismo papel (`VITE_API_TARGET`).
- El backend expone `/health` para las sondas de Docker y del balanceador.
