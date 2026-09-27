"""Pruebas del adaptador de Twilio con la capa HTTP simulada."""

import httpx
import pytest

from app.domain.value_objects.phone_number import PhoneNumber
from app.infrastructure.notifications.logging_sender import LoggingNotificationSender
from app.infrastructure.notifications.twilio_whatsapp_sender import TwilioWhatsAppSender

pytestmark = pytest.mark.unit

PHONE = PhoneNumber.parse("8112345678")


@pytest.fixture
def sender():
    return TwilioWhatsAppSender(
        account_sid="AC123", auth_token="secreto", sender="whatsapp:+14155238886"
    )


def fake_response(status_code: int) -> httpx.Response:
    return httpx.Response(status_code, request=httpx.Request("POST", "https://api.twilio.com"))


def test_a_successful_response_reports_delivery(sender, monkeypatch):
    monkeypatch.setattr(httpx, "post", lambda *a, **k: fake_response(201))

    assert sender.send(PHONE, "Hola") is True


def test_a_rejected_message_reports_failure(sender, monkeypatch):
    monkeypatch.setattr(httpx, "post", lambda *a, **k: fake_response(400))

    assert sender.send(PHONE, "Hola") is False


def test_a_network_error_never_propagates(sender, monkeypatch):
    # Una caida de red no debe tumbar la operacion de negocio que la invoco.
    def explode(*args, **kwargs):
        raise httpx.ConnectError("sin conexion")

    monkeypatch.setattr(httpx, "post", explode)

    assert sender.send(PHONE, "Hola") is False


def test_the_recipient_uses_the_whatsapp_scheme(sender, monkeypatch):
    captured = {}

    def capture(url, **kwargs):
        captured.update(kwargs["data"])
        return fake_response(201)

    monkeypatch.setattr(httpx, "post", capture)
    sender.send(PHONE, "Hola")

    assert captured["To"] == "whatsapp:+5218112345678"


def test_the_logging_sender_always_succeeds():
    assert LoggingNotificationSender().send(PHONE, "Hola") is True
