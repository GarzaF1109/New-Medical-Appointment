"""Adaptador de notificaciones sobre la API de WhatsApp de Twilio."""

from __future__ import annotations

import logging

import httpx

from app.domain.ports.notifications import NotificationSender
from app.domain.value_objects.phone_number import PhoneNumber

logger = logging.getLogger(__name__)

_TWILIO_API = "https://api.twilio.com/2010-04-01"
_TIMEOUT_SECONDS = 10.0


class TwilioWhatsAppSender(NotificationSender):
    """Envia mensajes de WhatsApp a traves de Twilio.

    Implementa `NotificationSender`, por lo que los casos de uso dependen de la
    interfaz y no de esta clase. Sustituirla por otro proveedor no requiere
    tocar la capa de aplicacion.
    """

    def __init__(self, *, account_sid: str, auth_token: str, sender: str) -> None:
        """Configura el cliente.

        Args:
            account_sid: SID de la cuenta Twilio.
            auth_token: Token de autenticacion.
            sender: Remitente en formato `whatsapp:+52...`.
        """
        self._account_sid = account_sid
        self._auth_token = auth_token
        self._sender = sender

    def send(self, phone: PhoneNumber, message: str) -> bool:
        """Entrega el mensaje, absorbiendo cualquier fallo del proveedor."""
        url = f"{_TWILIO_API}/Accounts/{self._account_sid}/Messages.json"
        payload = {
            "From": self._sender,
            "To": f"whatsapp:{phone.to_e164()}",
            "Body": message,
        }

        try:
            response = httpx.post(
                url,
                data=payload,
                auth=(self._account_sid, self._auth_token),
                timeout=_TIMEOUT_SECONDS,
            )
        except httpx.HTTPError as exc:
            logger.error("Error de red enviando WhatsApp a %s: %s", phone, exc)
            return False

        if response.is_success:
            logger.info("WhatsApp entregado a %s", phone)
            return True

        logger.error(
            "Twilio rechazo el mensaje a %s [%s]: %s",
            phone,
            response.status_code,
            response.text,
        )
        return False
