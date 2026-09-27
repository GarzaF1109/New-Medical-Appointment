"""Puerto de notificaciones salientes."""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.value_objects.phone_number import PhoneNumber


class NotificationSender(ABC):
    """Contrato para enviar mensajes a un paciente.

    Abstrae al proveedor concreto (Twilio, correo, SMS...). Gracias a esto los
    casos de uso se prueban con un doble en memoria y sin tocar la red, algo
    imposible con el metodo estatico `WhatsAppService::sendMessage()` anterior.
    """

    @abstractmethod
    def send(self, phone: PhoneNumber, message: str) -> bool:
        """Envia un mensaje.

        Args:
            phone: Destinatario ya normalizado.
            message: Cuerpo del mensaje en texto plano.

        Returns:
            True si el proveedor acepto el mensaje. Nunca lanza excepcion: una
            notificacion fallida no debe abortar la operacion de negocio.
        """
