"""Adaptador de notificaciones que solo registra en bitacora."""

from __future__ import annotations

import logging

from app.domain.ports.notifications import NotificationSender
from app.domain.value_objects.phone_number import PhoneNumber

logger = logging.getLogger(__name__)


class LoggingNotificationSender(NotificationSender):
    """Escribe el mensaje en el log en vez de enviarlo.

    Es el adaptador por defecto cuando no hay credenciales de Twilio, de modo
    que el sistema arranca en local sin secretos y sin gastar mensajes reales.
    """

    def send(self, phone: PhoneNumber, message: str) -> bool:
        logger.info("[NOTIFICACION SIMULADA] Para %s: %s", phone, message)
        return True
