"""Redaccion de los mensajes que se envian a los pacientes.

Separado de los casos de uso (SRP): cambiar el texto de un aviso no deberia
obligar a tocar la logica de agendado.
"""

from __future__ import annotations

from app.domain.entities.appointment import Appointment
from app.domain.entities.person import Doctor


def _format_slot(appointment: Appointment) -> tuple[str, str]:
    return (
        appointment.slot.date.strftime("%d/%m/%Y"),
        appointment.slot.start_time.strftime("%H:%M"),
    )


def appointment_scheduled(appointment: Appointment, doctor: Doctor) -> str:
    """Mensaje de confirmacion al agendar una cita."""
    date, time_ = _format_slot(appointment)
    return (
        f"Confirmacion de cita: Su cita medica ha sido registrada para el {date} "
        f"a las {time_} con el {doctor.display_name}. Motivo: {appointment.reason}"
    )


def appointment_rescheduled(appointment: Appointment, doctor: Doctor) -> str:
    """Mensaje de aviso al mover una cita de horario o de doctor."""
    date, time_ = _format_slot(appointment)
    return (
        f"Cambio en su cita: Su cita medica ha sido reagendada para el {date} "
        f"a las {time_} con el {doctor.display_name}. Motivo: {appointment.reason}"
    )


def appointment_cancelled(appointment: Appointment) -> str:
    """Mensaje de aviso al cancelar una cita."""
    date, time_ = _format_slot(appointment)
    return (
        f"Aviso: Su cita medica del {date} a las {time_} ha sido cancelada. "
        f"Si tiene dudas, contacte a la clinica."
    )


def appointment_reminder(appointment: Appointment, doctor: Doctor) -> str:
    """Recordatorio enviado 24 horas antes de la cita."""
    date, time_ = _format_slot(appointment)
    return (
        f"Recordatorio: Tiene una cita medica manana {date} a las {time_} "
        f"con el {doctor.display_name}. Por favor, confirme su asistencia."
    )
