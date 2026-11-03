"""Tipos de parametros de ruta compartidos.

`ResourceId` acota el identificador numerico al rango de un `INTEGER` de
Postgres. Sin este limite, un ID fuera de rango (`/patients/999999999999999999`)
llegaba sin validar hasta la base de datos, que lo rechazaba con un error de
rango que el manejador generico traducia a `500` en vez de `422`. Lo encontro
OWASP ZAP en la primera corrida (ver `docs/security/owasp-zap.md`).
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Path

# Limite superior de `INTEGER` en PostgreSQL (columna usada para los IDs).
POSTGRES_INT_MAX = 2_147_483_647

ResourceId = Annotated[
    int,
    Path(ge=1, le=POSTGRES_INT_MAX, description="Identificador numerico del recurso."),
]
