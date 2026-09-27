"""Instrumentacion con OpenTelemetry.

La guia AIVARA pide trazas, metricas y logs correlacionados. La instrumentacion
es opcional (`OTEL_ENABLED`) para que el entorno local no dependa de un
colector levantado.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def configure_telemetry(app, *, service_name: str, endpoint: str) -> None:
    """Instrumenta la aplicacion FastAPI y el cliente SQLAlchemy.

    Args:
        app: Instancia de FastAPI a instrumentar.
        service_name: Nombre con el que el servicio aparece en las trazas.
        endpoint: Destino OTLP del colector.
    """
    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
            OTLPSpanExporter,
        )
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
    except ImportError:
        logger.warning(
            "OTEL_ENABLED esta activo pero las dependencias de OpenTelemetry no "
            "estan instaladas. Instale el extra 'observability'."
        )
        return

    provider = TracerProvider(resource=Resource.create({"service.name": service_name}))
    provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint)))
    trace.set_tracer_provider(provider)

    FastAPIInstrumentor.instrument_app(app)
    SQLAlchemyInstrumentor().instrument()
    logger.info("OpenTelemetry activo; exportando a %s", endpoint)
