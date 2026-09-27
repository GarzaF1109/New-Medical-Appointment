# Sistema de Gestion de Citas Medicas

Reimplementacion del sistema `medical-appointment-app` (Laravel + Livewire) sobre
**FastAPI + React**, siguiendo la *Guia de Mejores Practicas de Ingenieria de
Software* de AIVARA.

## Arranque rapido

```bash
docker compose up --build
```

| Servicio | URL |
|---|---|
| Interfaz web | <http://localhost:8080> |
| API | <http://localhost:8000> |
| Swagger | <http://localhost:8000/docs> |

Para desarrollo local sin Docker, ver [`docs/development/setup.md`](docs/development/setup.md).

## Estructura

```
newmedicalappointmentapp/
├── backend/
│   ├── src/app/
│   │   ├── domain/           # Entidades, value objects, excepciones, PUERTOS
│   │   ├── application/      # Casos de uso, DTOs, redaccion de mensajes
│   │   ├── infrastructure/   # SQLAlchemy, Twilio, reloj, config, OTel
│   │   └── presentation/     # Routers, esquemas, errores HTTP, DI
│   └── tests/
│       ├── unit/             # Sin E/S — 129 pruebas
│       └── integration/      # API + base de datos — 61 pruebas
├── frontend/
│   └── src/
│       ├── api/              # Cliente HTTP tipado y errores
│       ├── features/         # Modulo de citas: componentes y hooks
│       ├── components/       # Componentes compartidos
│       └── pages/
├── docs/                     # C4, ADRs, contrato de API, guias
├── ops/                      # Configuracion de OTel y Prometheus
└── docker-compose.yml
```

## Arquitectura en capas

```
PRESENTACION  ──▶  APLICACION  ──▶  DOMINIO  ◀──  INFRAESTRUCTURA
   routers          casos de uso     entidades      SQLAlchemy
   esquemas         DTOs             value objects  Twilio
   errores HTTP     mensajes         PUERTOS (ABC)  reloj · OTel
```

La flecha de infraestructura apunta **hacia el dominio**: es la inversion de
dependencias. El dominio declara los puertos que necesita y la infraestructura se
adapta. Por eso `domain/` no importa SQLAlchemy, httpx ni FastAPI, y sus reglas se
prueban sin levantar nada.

Detalle en [`docs/architecture/components.md`](docs/architecture/components.md).

## Estado

| Metrica | Valor |
|---|---|
| Pruebas backend | 190 en verde |
| Cobertura backend | 94% (umbral exigido: 80%) |
| Pruebas frontend | 14 en verde |
| Linter | `ruff check` sin hallazgos |
| Tipos | `tsc --noEmit` sin errores |

```bash
cd backend  && pytest --cov     # 113 passed · 93%
cd frontend && npm test         # 14 passed
```

## Que cambio respecto al sistema Laravel

| Sistema anterior | Ahora | Por que |
|---|---|---|
| Regla de conflicto duplicada en `AppointmentCreate` y `AppointmentEdit` | Una sola: `TimeSlot.overlaps()` | DRY; no pueden divergir |
| `WhatsAppService::sendMessage()` estatico | Puerto `NotificationSender` inyectado | Se prueba sin red |
| `POST /appointments/{id}/move-to-24hours` | `PATCH /appointments/{id}` | Sustantivos, no verbos |
| `move-to-24hours` no revalidaba conflictos | El reagendado siempre revalida | Corrige un defecto real |
| `start_time`, `end_time` y `duration` persistidos | `end_time` derivado | Imposible que se contradigan |
| `session()->flash('swal')` como manejo de errores | Excepciones de negocio → HTTP | Contrato de error uniforme |
| Modelos Eloquent (ActiveRecord) | Entidades + repositorios | Reglas probables sin base de datos |
| Sin API ni OpenAPI | REST `/api/v1` con Swagger automatico | Documentacion que no se desincroniza |
| Sin pruebas de negocio | 113 pruebas, 93% de cobertura | Piramide de pruebas de la guia |

## Alcance actual

Implementado de punta a punta el **modulo de Citas**: agendar, listar, filtrar,
reagendar, reasignar, confirmar, atender, cancelar, eliminar y recordatorios
automaticas, mas los catalogos de lectura de pacientes y doctores.

Pendientes, siguiendo el mismo patron por capas: CRUD de Pacientes, Doctores,
Consultas (con recetas), Seguros y Usuarios; autenticacion JWT y RBAC.

## Documentacion

Ver [`docs/`](docs/README.md) — C4, cinco ADRs, contrato de API y guias de
desarrollo.
