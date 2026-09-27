# Puesta en marcha

## Requisitos

| Herramienta | Version | Para que |
|---|---|---|
| Python | 3.12 o superior | Backend |
| Node.js | 22 o superior | Frontend |
| Docker | 27 o superior | Opcional: pila completa con PostgreSQL |

## Opcion A — Todo con Docker (lo mas rapido)

```bash
docker compose up --build
```

- Frontend: <http://localhost:8080>
- API: <http://localhost:8000>
- Swagger: <http://localhost:8000/docs>

## Opcion B — Local, dos terminales

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # o: uv venv .venv
pip install -e ".[dev]"                             # o: uv pip install -e ".[dev]"

cp .env.example .env
python -m app.infrastructure.persistence.seed       # datos de ejemplo

uvicorn app.main:app --reload
```

Queda en <http://localhost:8000>, con Swagger en `/docs`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Queda en <http://localhost:5173>. Vite hace proxy de `/api` al backend, asi que no
hay que configurar CORS. Si el backend corre en otro puerto:

```bash
VITE_API_TARGET=http://localhost:8899 npm run dev
```

## Verificaciones

```bash
# Backend
cd backend
pytest                        # 113 pruebas
pytest --cov                  # cobertura; falla por debajo del 80%
pytest -m unit                # solo unitarias
ruff check src tests          # linter

# Frontend
cd frontend
npm test                      # 14 pruebas
npx tsc -b --noEmit           # verificacion de tipos
npm run build                 # compilacion de produccion
```

## Notificaciones por WhatsApp

Sin credenciales de Twilio en `.env`, la aplicacion usa `LoggingNotificationSender`,
que escribe el mensaje en la bitacora en lugar de enviarlo. **El entorno local
funciona completo y sin secretos.**

Para enviar de verdad, complete en `.env`:

```
TWILIO_ACCOUNT_SID=ACxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxx
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
```

`.env` esta en `.gitignore`. Nunca lo versione.

## Observabilidad (opcional)

```bash
cd backend && pip install -e ".[observability]"
docker compose -f docker-compose.yml -f docker-compose.observability.yml up
```

Trazas en Jaeger (<http://localhost:16686>), metricas en Prometheus
(<http://localhost:9090>).
