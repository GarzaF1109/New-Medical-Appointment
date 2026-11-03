# Guia paso a paso — levantar el proyecto y correr todo

Esta guia es para la expo: levantar el sistema desde cero y ejecutar, en
orden, los seis puntos del enunciado (arquitectura, stack, ZAP, Burp,
Playwright, automatizacion). Cada seccion trae los comandos exactos.

Requisito unico: **Docker** corriendo (Docker Desktop abierto). Node solo
hace falta si vas a correr Playwright fuera de Docker (recomendado, es mas
rapido de iterar).

---

## 1. Levantar el proyecto

```bash
cd /Users/fernandogarza/Projects/TecDeSoftware/newmedicalappointmentapp

docker compose up --build -d
```

La primera vez tarda unos minutos (construye las imagenes). Espera a que
responda:

```bash
for i in $(seq 1 30); do
  curl -fs http://localhost:8000/health && break
  sleep 1
done
```

Deberia imprimir `{"status":"ok","environment":"docker"}`.

### Verificar que todo esta arriba

```bash
docker compose ps
```

Las tres filas (`db`, `backend`, `frontend`) deben decir `healthy`/`running`.

| Servicio | URL |
|---|---|
| Interfaz web | <http://localhost:8080> |
| Swagger (API interactiva) | <http://localhost:8000/docs> |
| Especificacion OpenAPI | <http://localhost:8000/openapi.json> |

> La base arranca vacia. Entra a **Pacientes** y **Doctores** para dar de
> alta al menos uno de cada uno antes de agendar una cita.

---

## 2. Decisiones arquitectonicas y stack tecnologico (puntos 1 y 2)

No hay nada que correr: son documentos. Para la expo, abre:

- [`docs/architecture/decisions/`](docs/architecture/decisions/) — 7 ADRs
  (incluye el ADR-007 de la estrategia de seguridad/E2E de esta guia).
- [`docs/architecture/components.md`](docs/architecture/components.md),
  [`containers.md`](docs/architecture/containers.md),
  [`context.md`](docs/architecture/context.md) — diagramas C4.
- El propio [`README.md`](README.md) resume el stack (FastAPI + React +
  Postgres) y que cambio respecto al sistema Laravel anterior.

---

## 3. Pruebas unitarias e integracion (backend y frontend)

Estas no son parte de los 6 puntos pero son la base de todo lo demas — si
algo esta roto aqui, nada de lo de abajo va a servir.

El repo ya trae un entorno virtual con todo instalado en `backend/.venv`.
Si existe, solo actívalo:

```bash
cd backend
source .venv/bin/activate
pytest --cov                  # 220 pruebas, cobertura >= 80%
deactivate
cd ..
```

Si `.venv` no existe (clon nuevo del repo), créalo primero:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m ensurepip --upgrade
pip install -e ".[dev]"
pytest --cov
deactivate
cd ..
```

> En Mac, `pip`/`pip3` a veces no esta en el PATH fuera de un venv (es el
> caso de Homebrew sin un venv activo) — por eso el comando activa el venv
> primero en vez de llamar `pip` directo.

```bash
cd frontend
npm install                   # solo la primera vez, o si package.json cambio
npm test                      # pruebas unitarias con Vitest
cd ..
```

---

## 4. Pruebas E2E con Playwright (punto 5)

### 4.1 Instalar (solo la primera vez)

```bash
cd frontend
npm install
npx playwright install --with-deps chromium
cd ..
```

### 4.2 Correr contra la pila de Docker (igual que en CI)

Con el proyecto ya levantado (paso 1):

```bash
cd frontend
E2E_BASE_URL=http://localhost:8080 npm run test:e2e
cd ..
```

Salida esperada: `9 passed`. Cubre pacientes, doctores y el camino completo
de citas (agendar → confirmar → reagendar → cancelar → eliminar, mas el
409 de traslape de horario).

### 4.3 Ver el reporte HTML despues de correr

```bash
cd frontend
npx playwright show-report
cd ..
```

Abre un reporte navegable en el navegador con cada paso, captura de
pantalla y traza de los tests que fallaron (si alguno falla).

### 4.4 Modo interactivo (para ver los tests correr paso a paso, ideal para la expo en vivo)

```bash
cd frontend
E2E_BASE_URL=http://localhost:8080 npm run test:e2e:ui
cd ..
```

Abre la UI de Playwright: se puede correr un test a la vez y ver el
navegador moviendose en tiempo real, con el DOM y la linea de tiempo de cada
accion. Es la forma mas vistosa de mostrarlo en vivo.

### 4.5 Correr un solo archivo o un solo test

```bash
cd frontend
npx playwright test --config=e2e/playwright.config.ts e2e/tests/appointments.spec.ts
npx playwright test --config=e2e/playwright.config.ts -g "traslape de horario"
cd ..
```

Mas detalle de que cubre cada archivo y por que esta escrito asi:
[`docs/testing/e2e.md`](docs/testing/e2e.md).

---

## 5. OWASP ZAP — analisis automatizado (punto 3)

Con el proyecto ya levantado (paso 1):

```bash
./ops/zap/run-zap.sh
```

Tarda varios minutos (descarga la imagen `zaproxy/zap-stable` la primera
vez, despues corre el API scan y el baseline scan). Al terminar, abre los
reportes:

```bash
open docs/security/zap-reports/api-report.html
open docs/security/zap-reports/baseline-report.html
```

(En Linux usa `xdg-open` en vez de `open`.)

Que hace cada scan y por que se eligieron estos dos (y no un *full active
scan*): [`docs/security/owasp-zap.md`](docs/security/owasp-zap.md). Ahi
tambien esta el resultado de la primera corrida real (0 hallazgos graves,
11 advertencias menores, mas un `500` real con IDs fuera de rango que vale
la pena mencionar en la expo).

---

## 6. Burp Suite — analisis dinamico manual (punto 4)

Esto lo haces tu, a mano, con el proyecto levantado (paso 1):

1. Configura el navegador para usar el proxy de Burp (`127.0.0.1:8080` por
   defecto).
2. Navega <http://localhost:8080> una vez con el proxy activo.
3. Sigue el checklist caso por caso:
   [`docs/security/burp-manual-testing.md`](docs/security/burp-manual-testing.md).

El checklist ya trae los endpoints exactos, los payloads a probar y que
resultado esperar en cada categoria del Top 10 de OWASP.

---

## 7. Automatizacion — CI (punto 6)

No hay que correr nada local para este punto: cada `push`/PR a `main` o
`dev` dispara `.github/workflows/ci.yml`, que corre:

| Job | Que hace | ¿Bloquea el pipeline? |
|---|---|---|
| `backend` | lint + tipos + pytest con cobertura | Si |
| `frontend` | tipos + Vitest + build | Si |
| `docker` | build de imagenes + healthcheck | Si |
| `e2e` | Playwright contra `docker compose` | Si |
| `security-zap` | ZAP API scan + baseline scan | No (solo reporta) |

Para mostrarlo en la expo sin depender de internet: abre
`.github/workflows/ci.yml` y explica la tabla de arriba, o entra a la
pestaña **Actions** del repo en GitHub y muestra una corrida reciente con
los artefactos descargables (`playwright-report`, `zap-reports`).

Por que ZAP reporta pero no bloquea, y Playwright si: ver
[ADR-007](docs/architecture/decisions/ADR-007-estrategia-de-pruebas-de-seguridad-y-e2e.md).

---

## 8. Apagar todo al terminar

```bash
docker compose down        # apaga y conserva los datos de Postgres
docker compose down -v     # apaga y borra la base de datos tambien
```

---

## Referencia rapida de comandos

```bash
# Levantar
docker compose up --build -d

# Pruebas backend
cd backend && source .venv/bin/activate && pytest --cov && deactivate && cd ..

# Pruebas unitarias frontend
cd frontend && npm test

# Playwright — instalar (una vez)
cd frontend && npm install && npx playwright install --with-deps chromium

# Playwright — correr contra Docker
cd frontend && E2E_BASE_URL=http://localhost:8080 npm run test:e2e

# Playwright — ver reporte / modo interactivo
cd frontend && npx playwright show-report
cd frontend && E2E_BASE_URL=http://localhost:8080 npm run test:e2e:ui

# OWASP ZAP
./ops/zap/run-zap.sh
open docs/security/zap-reports/api-report.html
open docs/security/zap-reports/baseline-report.html

# Apagar
docker compose down
```

## Troubleshooting

| Sintoma | Causa probable | Solucion |
|---|---|---|
| `port is already allocated` | 8080/8000/5432 ocupados | Libera el puerto o cambia el mapeo en `docker-compose.yml` |
| Playwright: `Error: browserType.launch: Executable doesn't exist` | Faltan los navegadores | `npx playwright install --with-deps chromium` |
| Playwright: tests fallan con `strict mode violation` | Selector ambiguo (poco comun si no tocaste los specs) | Revisa [`docs/testing/e2e.md`](docs/testing/e2e.md), seccion "Decisiones de diseño" |
| `run-zap.sh`: se queda esperando el health check | El backend no termino de levantar | Corre `docker compose logs backend` y confirma que no truena al iniciar |
| `docker: Cannot connect to the Docker daemon` | Docker Desktop no esta corriendo | Abre Docker Desktop y reintenta |
| `zsh: command not found: pip` | En Mac, `pip` no esta en el PATH fuera de un venv | `source backend/.venv/bin/activate` antes de usar `pip`/`pytest` (ver seccion 3) |
