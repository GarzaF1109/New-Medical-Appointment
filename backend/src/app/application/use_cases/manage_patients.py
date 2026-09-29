"""Casos de uso del catalogo de pacientes: alta, edicion y baja."""

from __future__ import annotations

from datetime import date as Date

from app.domain.entities.person import Patient
from app.domain.exceptions import ConflictException, InvalidInputException, NotFoundException
from app.domain.ports.clock import Clock
from app.domain.ports.repositories import AppointmentRepository, PatientRepository
from app.domain.value_objects.birth_date import BirthDate
from app.domain.value_objects.phone_number import PhoneNumber

# Cota alta: solo sirve para saber si la agenda esta vacia, no para paginar.
_AGENDA_PROBE_LIMIT = 1000


def _build_birth_date(value: Date, today: Date) -> BirthDate:
    """Construye una fecha de nacimiento y comprueba que sea plausible hoy.

    Raises:
        InvalidInputException: Si la fecha esta en el futuro o implica una edad
            imposible.
    """
    birth_date = BirthDate(value)
    if birth_date.is_in_the_future(today):
        raise InvalidInputException("La fecha de nacimiento no puede estar en el futuro.")
    if birth_date.is_implausible_on(today):
        raise InvalidInputException("La fecha de nacimiento implica una edad imposible.")
    return birth_date


class CreatePatientUseCase:
    """Da de alta un paciente."""

    def __init__(self, *, patients: PatientRepository, clock: Clock) -> None:
        self._patients = patients
        self._clock = clock

    def execute(self, *, full_name: str, birth_date: Date, phone: str | None = None) -> Patient:
        """Registra un paciente nuevo.

        Args:
            full_name: Nombre completo.
            birth_date: Fecha de nacimiento.
            phone: Telefono de contacto en texto libre. None si no se captura.

        Returns:
            El paciente persistido, ya con su identificador.

        Raises:
            InvalidInputException: Si algun dato viola una invariante del
                dominio (nombre corto, fecha futura, telefono mal formado).
        """
        today = self._clock.now().date()
        patient = Patient(
            id=None,
            full_name=full_name,
            birth_date=_build_birth_date(birth_date, today),
            phone=PhoneNumber.parse(phone) if phone else None,
        )
        return self._patients.add(patient)


class UpdatePatientUseCase:
    """Edita los datos de un paciente existente."""

    def __init__(self, *, patients: PatientRepository, clock: Clock) -> None:
        self._patients = patients
        self._clock = clock

    def execute(
        self,
        patient_id: int,
        *,
        full_name: str | None = None,
        birth_date: Date | None = None,
        phone: str | None = None,
        clear_phone: bool = False,
    ) -> Patient:
        """Aplica una edicion parcial sobre el paciente indicado.

        Args:
            patient_id: Identificador del paciente.
            full_name: Nuevo nombre, o None para conservarlo.
            birth_date: Nueva fecha de nacimiento, o None para conservarla.
            phone: Nuevo telefono, o None para conservarlo.
            clear_phone: True para borrar el telefono registrado.

        Returns:
            El paciente ya actualizado.

        Raises:
            NotFoundException: Si el paciente no existe.
            InvalidInputException: Si algun dato nuevo es invalido.
        """
        current = self._patients.get(patient_id)
        if current is None:
            raise NotFoundException("Paciente", patient_id)

        today = self._clock.now().date()
        updated = current.with_changes(
            full_name=full_name,
            birth_date=None if birth_date is None else _build_birth_date(birth_date, today),
            phone=PhoneNumber.parse(phone) if phone else None,
            clear_phone=clear_phone,
        )
        return self._patients.update(updated)


class DeletePatientUseCase:
    """Da de baja a un paciente.

    Un paciente con citas vigentes no puede borrarse: hacerlo dejaria huecos en
    la agenda de los doctores. Primero hay que cancelar esas citas, que es la
    accion que conserva la trazabilidad clinica.
    """

    def __init__(self, *, patients: PatientRepository, appointments: AppointmentRepository) -> None:
        self._patients = patients
        self._appointments = appointments

    def execute(self, patient_id: int) -> None:
        """Elimina al paciente indicado.

        Raises:
            NotFoundException: Si el paciente no existe.
            ConflictException: Si conserva citas sin cancelar ni atender.
        """
        if self._patients.get(patient_id) is None:
            raise NotFoundException("Paciente", patient_id)

        agenda, _ = self._appointments.search(patient_id=patient_id, limit=_AGENDA_PROBE_LIMIT)
        if any(not appointment.status.is_final for appointment in agenda):
            raise ConflictException(
                "El paciente tiene citas vigentes; cancelelas antes de eliminarlo."
            )
        self._patients.delete(patient_id)
