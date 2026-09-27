"""Motor de base de datos y fabrica de sesiones."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.infrastructure.config import get_settings
from app.infrastructure.persistence.models import Base

_settings = get_settings()

_connect_args = {"check_same_thread": False} if _settings.database_url.startswith("sqlite") else {}

engine = create_engine(
    _settings.database_url,
    echo=_settings.debug,
    pool_pre_ping=True,
    connect_args=_connect_args,
)

SessionFactory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def create_schema() -> None:
    """Crea las tablas si no existen.

    Suficiente para desarrollo y pruebas. En despliegues reales el esquema lo
    gobierna Alembic; ver docs/architecture/decisions/ADR-003.
    """
    Base.metadata.create_all(bind=engine)


@contextmanager
def session_scope() -> Iterator[Session]:
    """Entrega una sesion transaccional que hace commit o rollback al salir."""
    session = SessionFactory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
