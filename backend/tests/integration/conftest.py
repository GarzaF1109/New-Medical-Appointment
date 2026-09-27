"""Fixtures de integracion: base de datos real y cliente HTTP."""

from __future__ import annotations

from datetime import date, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from tests.fakes import FrozenClock, SpyNotificationSender

from app.infrastructure.persistence.models import Base, DoctorModel, PatientModel
from app.main import create_app
from app.presentation.dependencies import (
    get_clock,
    get_notification_sender,
    get_session,
)

NOW = datetime(2026, 10, 1, 9, 0)


@pytest.fixture
def engine(tmp_path):
    """Motor SQLite sobre archivo temporal, recreado en cada prueba."""
    engine = create_engine(f"sqlite+pysqlite:///{tmp_path / 'test.db'}")
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def session_factory(engine):
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


@pytest.fixture
def seeded(session_factory):
    """Inserta el catalogo minimo de pacientes y doctores."""
    with session_factory() as session:
        session.add_all(
            [
                PatientModel(
                    id=1,
                    full_name="Ana Maria Lopez",
                    birth_date=date(1988, 3, 14),
                    phone="8112345678",
                ),
                PatientModel(
                    id=2,
                    full_name="Carlos Ramirez",
                    birth_date=date(1975, 11, 2),
                    phone="8187654321",
                ),
                PatientModel(
                    id=3,
                    full_name="Lucia Sin Telefono",
                    birth_date=date(2001, 7, 23),
                    phone=None,
                ),
            ]
        )
        session.add_all(
            [
                DoctorModel(id=1, full_name="Elena Navarro", speciality="Cardiologia"),
                DoctorModel(id=2, full_name="Roberto Diaz", speciality="Pediatria"),
            ]
        )
        session.commit()


@pytest.fixture
def notifier():
    return SpyNotificationSender()


@pytest.fixture
def client(session_factory, seeded, notifier):
    """Cliente HTTP con la base y el reloj de prueba inyectados.

    Se sobrescriben unicamente los adaptadores de infraestructura; los routers,
    casos de uso y entidades son exactamente los de produccion.
    """
    app = create_app()

    def override_session():
        session = session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    app.dependency_overrides[get_session] = override_session
    app.dependency_overrides[get_notification_sender] = lambda: notifier
    app.dependency_overrides[get_clock] = lambda: FrozenClock(NOW)

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
