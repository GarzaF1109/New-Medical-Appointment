# Sistema de Gestion de Citas Medicas

Reimplementacion del sistema `medical-appointment-app` (Laravel + Livewire) sobre
**FastAPI + React**, siguiendo la *Guia de Mejores Practicas de Ingenieria de
Software* de AIVARA.

## Como levantar el proyecto

### Requisitos previos

Solo hace falta **Docker** (version 27 o superior) con el demonio corriendo. No
hay que instalar Python ni Node: todo se compila dentro de los contenedores.

```bash
docker --version          # debe responder; si no, abra Docker Desktop
```

### Paso 1 — Clonar el repositorio

```bash
git clone https://github.com/GarzaF1109/New-Medical-Appointment.git
cd New-Medical-Appointment
```

### Paso 2 — Levantar la pila

```bash
docker compose up --build
```

La primera vez tarda unos minutos porque construye las imagenes. Esta listo
cuando la bitacora deja de avanzar y aparece `Application startup complete`.
Para dejarlo corriendo en segundo plano, agregue `-d`.

### Paso 3 — Comprobar que responde

```bash
curl http://localhost:8000/health     # {"status":"ok","environment":"docker"}
docker compose ps                     # db y backend en estado "healthy"
```

### Paso 4 — Abrir la aplicacion

| Servicio | URL |
|---|---|
| Interfaz web | <http://localhost:8080> |
| Swagger (API interactiva) | <http://localhost:8080/docs> |
| API directa | <http://localhost:8000/api/v1/patients> · sonda: `/health` |

> **La base arranca vacia.** Entre a la seccion **Pacientes** y luego a
> **Doctores** para dar de alta al menos uno de cada uno; solo entonces el
> formulario de citas tendra opciones que elegir.

### Paso 5 — Detener

```bash
docker compose down        # apaga y conserva los datos
docker compose down -v     # apaga y borra la base de datos
```

### Si algo falla

| Sintoma | Causa probable | Solucion |
|---|---|---|
| `port is already allocated` | Los puertos 8080, 8000 o 5432 estan ocupados | Libere el puerto o cambie el mapeo en `docker-compose.yml` |
| `Cannot connect to the Docker daemon` | Docker no esta corriendo | Abra Docker Desktop y reintente |
| La interfaz carga pero sin datos | La base arranca vacia | Es lo esperado: cree un paciente y un doctor |
| Cambios que no se reflejan | Imagen cacheada | `docker compose up --build --force-recreate` |

Para desarrollo local sin Docker -con recarga en caliente- ver
[`docs/development/setup.md`](docs/development/setup.md).

La interfaz tiene tres secciones -**Citas**, **Pacientes** y **Doctores**- desde
las que se puede ejercer toda la API: CRUD de ambos catalogos, agendado,
reagendado, confirmacion, cancelacion y borrado de citas, y la agenda de cada
paciente y de cada doctor.

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
│       ├── features/         # Modulos de citas y de catalogos (pacientes/doctores)
│       ├── components/       # Componentes compartidos
│       └── pages/            # Citas · Pacientes · Doctores
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
| Pruebas frontend | 20 en verde |
| Linter | `ruff check` sin hallazgos |
| Tipos | `mypy src` y `tsc --noEmit` sin errores |

```bash
cd backend  && pytest --cov     # 190 passed · 94%
cd frontend && npm test         # 20 passed
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
| Sin pruebas de negocio | 190 pruebas, 94% de cobertura | Piramide de pruebas de la guia |

## Alcance actual

Implementados de punta a punta -dominio, aplicacion, API e interfaz- los tres
modulos que pide el enunciado:

- **Citas**: agendar, listar, filtrar, reagendar, reasignar, confirmar, atender,
  cancelar, eliminar y recordatorios automaticos.
- **Pacientes**: CRUD completo (nombre, fecha de nacimiento y contacto), con la
  edad derivada por el backend, mas el historial de citas de cada uno.
- **Doctores**: CRUD completo (nombre, especialidad y cedula) y su agenda.

La **regla de no traslape de horario** vive en el dominio (`TimeSlot.overlaps`),
se aplica tanto al agendar como al reagendar, trata los horarios como intervalos
semiabiertos `[inicio, fin)` -dos citas contiguas no chocan- y responde `409`.

Pendientes, siguiendo el mismo patron por capas: Consultas (con recetas), Seguros
y Usuarios; autenticacion JWT y RBAC.

## Documentacion

Ver [`docs/`](docs/README.md) — C4, cinco ADRs, contrato de API y guias de
desarrollo.
