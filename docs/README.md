# Documentacion

| Seccion | Contenido |
|---|---|
| [`architecture/context.md`](architecture/context.md) | C4 nivel 1 — actores y sistemas externos |
| [`architecture/containers.md`](architecture/containers.md) | C4 nivel 2 — contenedores desplegables |
| [`architecture/components.md`](architecture/components.md) | C4 nivel 3 — las cuatro capas y sus componentes |
| [`architecture/decisions/`](architecture/decisions/) | Registros de decisiones (ADRs) |
| [`development/setup.md`](development/setup.md) | Puesta en marcha |
| [`development/workflow.md`](development/workflow.md) | GitFlow, commits, revision de codigo |
| [`api/overview.md`](api/overview.md) | Contrato REST completo |

## Decisiones registradas

| ADR | Decision |
|---|---|
| [001](architecture/decisions/ADR-001-arquitectura-en-capas.md) | Arquitectura en capas con inversion de dependencias |
| [002](architecture/decisions/ADR-002-fastapi-y-react.md) | FastAPI para el backend, React para el frontend |
| [003](architecture/decisions/ADR-003-esquema-y-migraciones.md) | `end_time` derivado; Alembic para el esquema |
| [004](architecture/decisions/ADR-004-notificaciones-no-bloqueantes.md) | Una notificacion fallida no revierte la operacion |
| [005](architecture/decisions/ADR-005-api-rest-sin-verbos.md) | Transiciones de estado como subrecursos |
