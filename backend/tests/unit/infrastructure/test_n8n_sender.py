"""Pruebas del adaptador de notificaciones para n8n con HTTP simulado."""

import httpx
import pytest

from app.domain.value_objects.phone_number import PhoneNumber
from app.infrastructure.notifications.n8n_sender import N8nWebhookSender

pytestmark = pytest.mark.unit

PHONE = PhoneNumber.parse("8112345678")
WEBHOOK_URL = "http://localhost:5678/webhook/medical-appointment-notifications"


@pytest.fixture
def sender():
    return N8nWebhookSender(webhook_url=WEBHOOK_URL)


def fake_response(status_code: int) -> httpx.Response:
    return httpx.Response(status_code, request=httpx.Request("POST", WEBHOOK_URL))


def test_n8n_successful_webhook_response_reports_success(sender, monkeypatch):
    monkeypatch.setattr(httpx.Client, "post", lambda *a, **k: fake_response(200))

    assert sender.send(PHONE, "Cita confirmada") is True


def test_n8n_error_status_reports_failure_gracefully(sender, monkeypatch):
    monkeypatch.setattr(httpx.Client, "post", lambda *a, **k: fake_response(500))

    assert sender.send(PHONE, "Cita confirmada") is False


def test_n8n_network_error_never_raises_exception(sender, monkeypatch):
    def explode(*args, **kwargs):
        raise httpx.ConnectError("n8n no responde")

    monkeypatch.setattr(httpx.Client, "post", explode)

    assert sender.send(PHONE, "Cita confirmada") is False


def test_n8n_payload_structure(sender, monkeypatch):
    captured = {}

    def capture(client, url, json=None, **kwargs):
        captured["url"] = url
        captured["json"] = json
        return fake_response(200)

    monkeypatch.setattr(httpx.Client, "post", capture)
    sender.send(PHONE, "Recordatorio de cita")

    assert captured["url"] == WEBHOOK_URL
    assert captured["json"]["recipient_phone"] == "+5218112345678"
    assert captured["json"]["message"] == "Recordatorio de cita"
    assert captured["json"]["source"] == "medical_appointment_app"
