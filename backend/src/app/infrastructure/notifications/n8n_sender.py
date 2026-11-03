"""Adaptador de notificaciones salientes hacia flujos de automatizacion en n8n."""

from __future__ import annotations

import logging

import httpx

from app.domain.ports.notifications import NotificationSender
from app.domain.value_objects.phone_number import PhoneNumber

logger = logging.getLogger(__name__)


class N8nWebhookSender(NotificationSender):
    """Envia eventos de aviso a un webhook de n8n para orquestar la automatizacion.

    Cumple con el ADR-004: una falla en n8n o caida de red jamas aborta la operacion
    de negocio principal, solo se registra en bitacora y retorna False.
    """

    def __init__(self, webhook_url: str, timeout: float = 3.0) -> None:
        self.webhook_url = webhook_url
        self.timeout = timeout

    def send(self, phone: PhoneNumber, message: str) -> bool:
        """Emite el payload JSON al webhook configurado en n8n."""
        payload = {
            "recipient_phone": str(phone),
            "message": message,
            "source": "medical_appointment_app",
        }
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(self.webhook_url, json=payload)
                if response.status_code in (200, 201, 204):
                    logger.info("[N8N] Notificacion aceptada por webhook %s", self.webhook_url)
                    return True
                logger.warning(
                    "[N8N] Webhook devolvio estado HTTP %d: %s",
                    response.status_code,
                    response.text[:200],
                )
                return False
        except Exception as exc:
            logger.warning("[N8N] No se pudo entregar la notificacion a n8n: %s", exc)
            return False
