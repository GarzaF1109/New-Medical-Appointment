"""Casos de uso del catalogo de doctores: alta, edicion y baja."""

from __future__ import annotations

from app.domain.entities.person import Doctor
from app.domain.exceptions import ConflictException, NotFoundException
from app.domain.ports.repositories import AppointmentRepository, DoctorRepository
from app.domain.value_objects.medical_license import MedicalLicense

# Cota alta: solo sirve para saber si la agenda esta vacia, no para paginar.
_AGENDA_PROBE_LIMIT = 1000


class CreateDoctorUseCase:
    """Da de alta un doctor."""

    def __init__(self, *, doctors: DoctorRepository) -> None:
        self._doctors = doctors

    def execute(
        self, *, full_name: str, speciality: str, medical_license_number: str | None = None
    ) -> Doctor:
        """Registra un doctor nuevo.

        Args:
            full_name: Nombre completo.
            speciality: Especialidad medica.
            medical_license_number: Cedula profesional. None si no se captura.

        Returns:
            El doctor persistido, ya con su identificador.

        Raises:
            InvalidInputException: Si el nombre, la especialidad o la cedula no
                cumplen las invariantes del dominio.
        """
        doctor = Doctor(
            id=None,
            full_name=full_name,
            speciality=speciality,
            license=MedicalLicense(medical_license_number) if medical_license_number else None,
        )
        return self._doctors.add(doctor)


class UpdateDoctorUseCase:
    """Edita los datos de un doctor existente."""

    def __init__(self, *, doctors: DoctorRepository) -> None:
        self._doctors = doctors

    def execute(
        self,
        doctor_id: int,
        *,
        full_name: str | None = None,
        speciality: str | None = None,
        medical_license_number: str | None = None,
        clear_license: bool = False,
    ) -> Doctor:
        """Aplica una edicion parcial sobre el doctor indicado.

        Args:
            doctor_id: Identificador del doctor.
            full_name: Nuevo nombre, o None para conservarlo.
            speciality: Nueva especialidad, o None para conservarla.
            medical_license_number: Nueva cedula, o None para conservarla.
            clear_license: True para borrar la cedula registrada.

        Returns:
            El doctor ya actualizado.

        Raises:
            NotFoundException: Si el doctor no existe.
            InvalidInputException: Si algun dato nuevo es invalido.
        """
        current = self._doctors.get(doctor_id)
        if current is None:
            raise NotFoundException("Doctor", doctor_id)

        updated = current.with_changes(
            full_name=full_name,
            speciality=speciality,
            license=MedicalLicense(medical_license_number) if medical_license_number else None,
            clear_license=clear_license,
        )
        return self._doctors.update(updated)


class DeleteDoctorUseCase:
    """Da de baja a un doctor.

    Se aplica la misma cautela que con los pacientes: mientras el doctor
    conserve citas vigentes, borrarlo destruiria la agenda comprometida con esos
    pacientes.
    """

    def __init__(self, *, doctors: DoctorRepository, appointments: AppointmentRepository) -> None:
        self._doctors = doctors
        self._appointments = appointments

    def execute(self, doctor_id: int) -> None:
        """Elimina al doctor indicado.

        Raises:
            NotFoundException: Si el doctor no existe.
            ConflictException: Si conserva citas sin cancelar ni atender.
        """
        if self._doctors.get(doctor_id) is None:
            raise NotFoundException("Doctor", doctor_id)

        agenda, _ = self._appointments.list(doctor_id=doctor_id, limit=_AGENDA_PROBE_LIMIT)
        if any(not appointment.status.is_final for appointment in agenda):
            raise ConflictException(
                "El doctor tiene citas vigentes; cancelelas antes de eliminarlo."
            )
        self._doctors.delete(doctor_id)
