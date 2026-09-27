"""Carga de datos de ejemplo para desarrollo."""

from __future__ import annotations

import logging
from datetime import date

from sqlalchemy import select

from app.infrastructure.persistence.database import create_schema, session_scope
from app.infrastructure.persistence.models import DoctorModel, PatientModel

logger = logging.getLogger(__name__)

_PATIENTS = [
    ("Ana Maria Lopez", date(1988, 3, 14), "8112345678"),
    ("Carlos Ramirez Soto", date(1975, 11, 2), "8187654321"),
    ("Lucia Fernandez Cruz", date(2001, 7, 23), None),
    ("Miguel Angel Torres", date(1993, 1, 9), "5512349876"),
]

_DOCTORS = [
    ("Elena Navarro", "Cardiologia", "L-20260526-8845A"),
    ("Roberto Diaz Mena", "Pediatria", "L-20240113-1122B"),
    ("Sofia Herrera", "Medicina General", None),
]


def seed() -> None:
    """Inserta pacientes y doctores de ejemplo si la base esta vacia."""
    create_schema()
    with session_scope() as session:
        if session.scalar(select(PatientModel).limit(1)) is not None:
            logger.info("La base ya contiene datos; no se siembra nada.")
            return

        session.add_all(
            [
                PatientModel(full_name=name, birth_date=birth_date, phone=phone)
                for name, birth_date, phone in _PATIENTS
            ]
        )
        session.add_all(
            [
                DoctorModel(full_name=name, speciality=spec, medical_license_number=lic)
                for name, spec, lic in _DOCTORS
            ]
        )
        logger.info("Sembrados %s pacientes y %s doctores.", len(_PATIENTS), len(_DOCTORS))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    seed()
