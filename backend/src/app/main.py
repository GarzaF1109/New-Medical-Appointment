"""Punto de entrada de la API de citas medicas.

Ensambla la aplicacion FastAPI: middlewares, manejadores de error, routers
versionados y observabilidad. No contiene logica de negocio.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.infrastructure.config import get_settings
from app.infrastructure.observability.telemetry import configure_telemetry
from app.infrastructure.persistence.database import create_schema
from app.presentation.api.errors import register_exception_handlers
from app.presentation.api.v1.routers.appointments import router as appointments_router
from app.presentation.api.v1.routers.people import doctors_router, patients_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s [%(name)s] %(message)s",
)

API_V1_PREFIX = "/api/v1"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Prepara el esquema al arrancar y libera recursos al apagar."""
    create_schema()
    yield


def create_app() -> FastAPI:
    """Construye y configura la aplicacion.

    Se expone como fabrica para que las pruebas puedan crear instancias
    independientes con sus propias dependencias sobrescritas.
    """
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version="1.0.0",
        description=(
            "API de gestion de citas medicas. Construida sobre una arquitectura "
            "en capas (presentacion, aplicacion, dominio, infraestructura) segun "
            "la Guia de Mejores Practicas de Ingenieria de Software de AIVARA."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)

    app.include_router(appointments_router, prefix=API_V1_PREFIX)
    app.include_router(patients_router, prefix=API_V1_PREFIX)
    app.include_router(doctors_router, prefix=API_V1_PREFIX)

    if settings.otel_enabled:
        configure_telemetry(
            app,
            service_name=settings.app_name,
            endpoint=settings.otel_exporter_otlp_endpoint,
        )

    @app.get("/health", tags=["Operacion"], summary="Sonda de salud")
    def health() -> dict[str, str]:
        """Indica que el proceso responde. Lo consultan Docker y el balanceador."""
        return {"status": "ok", "environment": settings.environment}

    return app


app = create_app()
