"""Cableado de dependencias (composition root).

Es el unico modulo donde las implementaciones concretas se unen a las
interfaces. Los casos de uso jamas instancian a sus colaboradores: los reciben,
que es lo que permite sustituirlos por dobles en las pruebas.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.application.use_cases.change_appointment_status import (
    ChangeAppointmentStatusUseCase,
)
from app.application.use_cases.delete_appointment import DeleteAppointmentUseCase
from app.application.use_cases.manage_doctors import (
    CreateDoctorUseCase,
    DeleteDoctorUseCase,
    UpdateDoctorUseCase,
)
from app.application.use_cases.manage_patients import (
    CreatePatientUseCase,
    DeletePatientUseCase,
    UpdatePatientUseCase,
)
from app.application.use_cases.query_appointments import QueryAppointmentsUseCase
from app.application.use_cases.reschedule_appointment import RescheduleAppointmentUseCase
from app.application.use_cases.schedule_appointment import ScheduleAppointmentUseCase
from app.domain.ports.clock import Clock
from app.domain.ports.notifications import NotificationSender
from app.domain.ports.repositories import (
    AppointmentRepository,
    DoctorRepository,
    PatientRepository,
)
from app.infrastructure.clock import SystemClock
from app.infrastructure.config import Settings, get_settings
from app.infrastructure.notifications.logging_sender import LoggingNotificationSender
from app.infrastructure.notifications.twilio_whatsapp_sender import TwilioWhatsAppSender
from app.infrastructure.persistence.database import SessionFactory
from app.infrastructure.persistence.sqlalchemy_repositories import (
    SqlAlchemyAppointmentRepository,
    SqlAlchemyDoctorRepository,
    SqlAlchemyPatientRepository,
)


def get_session() -> Iterator[Session]:
    """Abre una sesion por peticion y confirma o revierte al terminar."""
    session = SessionFactory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


SessionDep = Annotated[Session, Depends(get_session)]
SettingsDep = Annotated[Settings, Depends(get_settings)]


def get_appointment_repository(session: SessionDep) -> AppointmentRepository:
    """Repositorio de citas ligado a la sesion de la peticion."""
    return SqlAlchemyAppointmentRepository(session)


def get_patient_repository(session: SessionDep) -> PatientRepository:
    """Repositorio de pacientes ligado a la sesion de la peticion."""
    return SqlAlchemyPatientRepository(session)


def get_doctor_repository(session: SessionDep) -> DoctorRepository:
    """Repositorio de doctores ligado a la sesion de la peticion."""
    return SqlAlchemyDoctorRepository(session)


def get_notification_sender(settings: SettingsDep) -> NotificationSender:
    """Elige el canal de notificacion segun la configuracion disponible.

    Sin credenciales de Twilio se usa el adaptador de bitacora, de modo que el
    entorno local funciona completo y sin secretos.
    """
    if settings.notifications_enabled:
        return TwilioWhatsAppSender(
            account_sid=settings.twilio_account_sid,
            auth_token=settings.twilio_auth_token,
            sender=settings.twilio_whatsapp_from,
        )
    return LoggingNotificationSender()


def get_clock() -> Clock:
    """Reloj del sistema."""
    return SystemClock()


AppointmentRepositoryDep = Annotated[AppointmentRepository, Depends(get_appointment_repository)]
PatientRepositoryDep = Annotated[PatientRepository, Depends(get_patient_repository)]
DoctorRepositoryDep = Annotated[DoctorRepository, Depends(get_doctor_repository)]
NotificationSenderDep = Annotated[NotificationSender, Depends(get_notification_sender)]
ClockDep = Annotated[Clock, Depends(get_clock)]


def get_schedule_use_case(
    appointments: AppointmentRepositoryDep,
    patients: PatientRepositoryDep,
    doctors: DoctorRepositoryDep,
    notifier: NotificationSenderDep,
    clock: ClockDep,
) -> ScheduleAppointmentUseCase:
    """Caso de uso de agendado, ya cableado."""
    return ScheduleAppointmentUseCase(
        appointments=appointments,
        patients=patients,
        doctors=doctors,
        notifier=notifier,
        clock=clock,
    )


def get_reschedule_use_case(
    appointments: AppointmentRepositoryDep,
    patients: PatientRepositoryDep,
    doctors: DoctorRepositoryDep,
    notifier: NotificationSenderDep,
    clock: ClockDep,
) -> RescheduleAppointmentUseCase:
    """Caso de uso de reagendado, ya cableado."""
    return RescheduleAppointmentUseCase(
        appointments=appointments,
        patients=patients,
        doctors=doctors,
        notifier=notifier,
        clock=clock,
    )


def get_status_use_case(
    appointments: AppointmentRepositoryDep,
    patients: PatientRepositoryDep,
    doctors: DoctorRepositoryDep,
    notifier: NotificationSenderDep,
) -> ChangeAppointmentStatusUseCase:
    """Caso de uso de transiciones de estado, ya cableado."""
    return ChangeAppointmentStatusUseCase(
        appointments=appointments,
        patients=patients,
        doctors=doctors,
        notifier=notifier,
    )


def get_query_use_case(
    appointments: AppointmentRepositoryDep,
    patients: PatientRepositoryDep,
    doctors: DoctorRepositoryDep,
) -> QueryAppointmentsUseCase:
    """Caso de uso de consulta, ya cableado."""
    return QueryAppointmentsUseCase(appointments=appointments, patients=patients, doctors=doctors)


ScheduleUseCaseDep = Annotated[ScheduleAppointmentUseCase, Depends(get_schedule_use_case)]
RescheduleUseCaseDep = Annotated[RescheduleAppointmentUseCase, Depends(get_reschedule_use_case)]
StatusUseCaseDep = Annotated[ChangeAppointmentStatusUseCase, Depends(get_status_use_case)]
QueryUseCaseDep = Annotated[QueryAppointmentsUseCase, Depends(get_query_use_case)]


def get_delete_use_case(appointments: AppointmentRepositoryDep) -> DeleteAppointmentUseCase:
    """Caso de uso de eliminacion, ya cableado."""
    return DeleteAppointmentUseCase(appointments=appointments)


DeleteUseCaseDep = Annotated[DeleteAppointmentUseCase, Depends(get_delete_use_case)]


def get_create_patient_use_case(
    patients: PatientRepositoryDep, clock: ClockDep
) -> CreatePatientUseCase:
    """Caso de uso de alta de pacientes, ya cableado."""
    return CreatePatientUseCase(patients=patients, clock=clock)


def get_update_patient_use_case(
    patients: PatientRepositoryDep, clock: ClockDep
) -> UpdatePatientUseCase:
    """Caso de uso de edicion de pacientes, ya cableado."""
    return UpdatePatientUseCase(patients=patients, clock=clock)


def get_delete_patient_use_case(
    patients: PatientRepositoryDep, appointments: AppointmentRepositoryDep
) -> DeletePatientUseCase:
    """Caso de uso de baja de pacientes, ya cableado."""
    return DeletePatientUseCase(patients=patients, appointments=appointments)


def get_create_doctor_use_case(doctors: DoctorRepositoryDep) -> CreateDoctorUseCase:
    """Caso de uso de alta de doctores, ya cableado."""
    return CreateDoctorUseCase(doctors=doctors)


def get_update_doctor_use_case(doctors: DoctorRepositoryDep) -> UpdateDoctorUseCase:
    """Caso de uso de edicion de doctores, ya cableado."""
    return UpdateDoctorUseCase(doctors=doctors)


def get_delete_doctor_use_case(
    doctors: DoctorRepositoryDep, appointments: AppointmentRepositoryDep
) -> DeleteDoctorUseCase:
    """Caso de uso de baja de doctores, ya cableado."""
    return DeleteDoctorUseCase(doctors=doctors, appointments=appointments)


CreatePatientUseCaseDep = Annotated[CreatePatientUseCase, Depends(get_create_patient_use_case)]
UpdatePatientUseCaseDep = Annotated[UpdatePatientUseCase, Depends(get_update_patient_use_case)]
DeletePatientUseCaseDep = Annotated[DeletePatientUseCase, Depends(get_delete_patient_use_case)]
CreateDoctorUseCaseDep = Annotated[CreateDoctorUseCase, Depends(get_create_doctor_use_case)]
UpdateDoctorUseCaseDep = Annotated[UpdateDoctorUseCase, Depends(get_update_doctor_use_case)]
DeleteDoctorUseCaseDep = Annotated[DeleteDoctorUseCase, Depends(get_delete_doctor_use_case)]
