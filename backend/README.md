# Backend — API de Citas Medicas

FastAPI + SQLAlchemy 2.0 + Pydantic v2, en arquitectura de cuatro capas.

## Comandos

```bash
pip install -e ".[dev]"                          # dependencias
cp .env.example .env                             # configuracion
python -m app.infrastructure.persistence.seed    # datos de ejemplo
uvicorn app.main:app --reload                    # servidor

pytest                    # todas las pruebas
pytest -m unit            # solo unitarias (sin E/S)
pytest -m integration     # API + base de datos
pytest --cov              # cobertura; falla por debajo del 80%
ruff check src tests      # linter
ruff format src tests     # formato
```

## Regla de oro

`src/app/domain/` **no importa** SQLAlchemy, httpx ni FastAPI. Si una importacion
de esas aparece ahi, la logica esta en la capa equivocada.

```bash
# Verificacion rapida en la revision de codigo:
! grep -rE "^(from|import) (sqlalchemy|fastapi|httpx|pydantic)" src/app/domain/
```

## Donde va cada cosa

| Necesito… | Va en… |
|---|---|
| Una regla de negocio nueva | `domain/entities/` o `domain/value_objects/` |
| Orquestar varios pasos | `application/use_cases/` |
| Hablar con un sistema externo | `infrastructure/`, detras de un puerto |
| Exponer algo por HTTP | `presentation/api/v1/` |
| Unir una interfaz con su implementacion | `presentation/dependencies.py` |
