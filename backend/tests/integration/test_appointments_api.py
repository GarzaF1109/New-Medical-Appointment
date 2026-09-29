"""Pruebas de integracion de los endpoints de citas."""

import pytest

pytestmark = pytest.mark.integration

VALID_PAYLOAD = {
    "patientId": 1,
    "doctorId": 1,
    "date": "2026-10-15",
    "startTime": "10:00:00",
    "reason": "Dolor de cabeza persistente desde hace una semana",
}


def test_scheduling_returns_201(client):
    response = client.post("/api/v1/appointments", json=VALID_PAYLOAD)

    assert response.status_code == 201


def test_the_response_derives_the_end_time(client):
    response = client.post("/api/v1/appointments", json=VALID_PAYLOAD)

    assert response.json()["endTime"] == "11:00:00"


def test_the_response_includes_discovery_links(client):
    response = client.post("/api/v1/appointments", json=VALID_PAYLOAD)

    links = response.json()["_links"]
    assert links["self"]["href"].startswith("/api/v1/appointments/")


def test_the_response_resolves_names(client):
    response = client.post("/api/v1/appointments", json=VALID_PAYLOAD)

    assert response.json()["doctorName"] == "Dr(a). Elena Navarro"


def test_double_booking_returns_409(client):
    client.post("/api/v1/appointments", json=VALID_PAYLOAD)

    response = client.post("/api/v1/appointments", json={**VALID_PAYLOAD, "startTime": "10:30:00"})

    assert response.status_code == 409


def test_the_conflict_body_follows_the_error_contract(client):
    client.post("/api/v1/appointments", json=VALID_PAYLOAD)

    body = client.post(
        "/api/v1/appointments", json={**VALID_PAYLOAD, "startTime": "10:30:00"}
    ).json()

    assert body == {
        "status": 409,
        "code": "CONFLICT",
        "message": "El doctor ya tiene una cita en ese horario.",
    }


def test_a_short_reason_returns_422(client):
    response = client.post("/api/v1/appointments", json={**VALID_PAYLOAD, "reason": "gripa"})

    assert response.status_code == 422


def test_validation_errors_list_the_offending_field(client):
    body = client.post("/api/v1/appointments", json={**VALID_PAYLOAD, "reason": "gripa"}).json()

    assert body["details"][0]["field"] == "reason"


def test_an_unknown_patient_returns_404(client):
    response = client.post("/api/v1/appointments", json={**VALID_PAYLOAD, "patientId": 999})

    assert response.status_code == 404


def test_scheduling_in_the_past_returns_422(client):
    response = client.post("/api/v1/appointments", json={**VALID_PAYLOAD, "date": "2020-01-01"})

    assert response.status_code == 422


def test_listing_returns_the_created_appointment(client):
    client.post("/api/v1/appointments", json=VALID_PAYLOAD)

    body = client.get("/api/v1/appointments").json()

    assert body["total"] == 1


def test_listing_filters_by_doctor(client):
    client.post("/api/v1/appointments", json=VALID_PAYLOAD)

    body = client.get("/api/v1/appointments", params={"doctorId": 2}).json()

    assert body["total"] == 0


def test_the_doctor_agenda_subresource_works(client):
    client.post("/api/v1/appointments", json=VALID_PAYLOAD)

    body = client.get("/api/v1/doctors/1/appointments").json()

    assert body["total"] == 1


def test_fetching_an_unknown_appointment_returns_404(client):
    response = client.get("/api/v1/appointments/999")

    assert response.status_code == 404


def test_rescheduling_updates_the_hour(client):
    created = client.post("/api/v1/appointments", json=VALID_PAYLOAD).json()

    response = client.patch(f"/api/v1/appointments/{created['id']}", json={"startTime": "15:00:00"})

    assert response.json()["startTime"] == "15:00:00"


def test_rescheduling_persists_across_requests(client):
    created = client.post("/api/v1/appointments", json=VALID_PAYLOAD).json()
    client.patch(f"/api/v1/appointments/{created['id']}", json={"startTime": "15:00:00"})

    body = client.get(f"/api/v1/appointments/{created['id']}").json()

    assert body["startTime"] == "15:00:00"


def test_cancelling_moves_to_the_cancelled_state(client):
    created = client.post("/api/v1/appointments", json=VALID_PAYLOAD).json()

    body = client.put(f"/api/v1/appointments/{created['id']}/cancellation").json()

    assert body["statusLabel"] == "Cancelada"


def test_cancelling_twice_returns_409(client):
    created = client.post("/api/v1/appointments", json=VALID_PAYLOAD).json()
    client.put(f"/api/v1/appointments/{created['id']}/cancellation")

    response = client.put(f"/api/v1/appointments/{created['id']}/cancellation")

    assert response.status_code == 409


def test_a_cancelled_slot_can_be_reused(client):
    created = client.post("/api/v1/appointments", json=VALID_PAYLOAD).json()
    client.put(f"/api/v1/appointments/{created['id']}/cancellation")

    response = client.post("/api/v1/appointments", json={**VALID_PAYLOAD, "patientId": 2})

    assert response.status_code == 201


def test_confirming_moves_to_the_confirmed_state(client):
    created = client.post("/api/v1/appointments", json=VALID_PAYLOAD).json()

    body = client.put(f"/api/v1/appointments/{created['id']}/confirmation").json()

    assert body["statusLabel"] == "Confirmada"


def test_deleting_returns_204(client):
    created = client.post("/api/v1/appointments", json=VALID_PAYLOAD).json()

    response = client.delete(f"/api/v1/appointments/{created['id']}")

    assert response.status_code == 204


def test_a_deleted_appointment_is_gone(client):
    created = client.post("/api/v1/appointments", json=VALID_PAYLOAD).json()
    client.delete(f"/api/v1/appointments/{created['id']}")

    assert client.get(f"/api/v1/appointments/{created['id']}").status_code == 404


def test_notifications_reach_the_adapter(client, notifier):
    client.post("/api/v1/appointments", json=VALID_PAYLOAD)

    assert notifier.call_count == 1


def test_a_patient_without_phone_is_reported_as_not_notified(client):
    body = client.post("/api/v1/appointments", json={**VALID_PAYLOAD, "patientId": 3}).json()

    assert body["notificationSent"] is False


def test_the_catalogs_are_available(client):
    assert len(client.get("/api/v1/doctors").json()) == 2
    assert len(client.get("/api/v1/patients").json()) == 3


def test_the_phone_is_normalised_on_read(client):
    body = client.get("/api/v1/patients/1").json()

    assert body["phone"] == "+5218112345678"


def test_the_health_probe_responds(client):
    assert client.get("/health").json()["status"] == "ok"


def test_the_openapi_document_is_generated(client):
    schema = client.get("/openapi.json").json()

    assert "/api/v1/appointments" in schema["paths"]


def test_a_reason_of_only_symbols_is_rejected(client):
    response = client.post("/api/v1/appointments", json={**VALID_PAYLOAD, "reason": "!!!!!!!!!!!!"})

    assert response.status_code == 422


def test_a_reason_of_only_digits_is_rejected(client):
    response = client.post("/api/v1/appointments", json={**VALID_PAYLOAD, "reason": "1234567890"})

    assert response.status_code == 422


def test_a_date_beyond_the_scheduling_horizon_is_rejected(client):
    response = client.post("/api/v1/appointments", json={**VALID_PAYLOAD, "date": "2099-01-01"})

    assert response.status_code == 422
