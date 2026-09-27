"""Caso de uso: eliminar una cita de forma definitiva."""

from __future__ import annotations

from app.domain.exceptions import NotFoundException
from app.domain.ports.repositories import AppointmentRepository


class DeleteAppointmentUseCase:
    """Borra una cita del sistema.

    Para el flujo normal de negocio es preferible cancelar -que conserva la
    trazabilidad clinica-; este caso de uso existe para depuracion
    administrativa de registros capturados por error.
    """

    def __init__(self, *, appointments: AppointmentRepository) -> None:
        self._appointments = appointments

    def execute(self, appointment_id: int) -> None:
        """Elimina la cita indicada.

        Raises:
            NotFoundException: Si la cita no existe.
        """
        if self._appointments.get(appointment_id) is None:
            raise NotFoundException("Cita", appointment_id)
        self._appointments.delete(appointment_id)
