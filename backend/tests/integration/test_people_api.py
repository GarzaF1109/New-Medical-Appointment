"""Pruebas de integracion del CRUD de pacientes y doctores."""

import pytest

pytestmark = pytest.mark.integration

NEW_PATIENT = {
    "fullName": "Sofia Herrera Luna",
    "birthDate": "1992-06-18",
    "phone": "8112345678",
}

NEW_DOCTOR = {
    "fullName": "Javier Mendoza",
    "speciality": "Dermatologia",
    "medicalLicenseNumber": "L-20240113-1122B",
}

APPOINTMENT = {
    "patientId": 1,
    "doctorId": 1,
    "date": "2026-10-15",
    "startTime": "10:00:00",
    "reason": "Dolor de cabeza persistente desde hace una semana",
}


# --- Pacientes -------------------------------------------------------------


def test_creating_a_patient_returns_201(client):
    response = client.post("/api/v1/patients", json=NEW_PATIENT)

    assert response.status_code == 201


def test_the_created_patient_echoes_its_birth_date(client):
    body = client.post("/api/v1/patients", json=NEW_PATIENT).json()

    assert body["birthDate"] == "1992-06-18"


def test_the_response_derives_the_age(client):
    # El reloj de prueba esta fijado al 1 de octubre de 2026.
    body = client.post("/api/v1/patients", json=NEW_PATIENT).json()

    assert body["age"] == 34


def test_the_created_patient_normalises_the_phone(client):
    body = client.post("/api/v1/patients", json=NEW_PATIENT).json()

    assert body["phone"] == "+528112345678".replace("+52", "+521")


def test_a_created_patient_persists_across_requests(client):
    created_id = client.post("/api/v1/patients", json=NEW_PATIENT).json()["id"]

    assert client.get(f"/api/v1/patients/{created_id}").status_code == 200


def test_a_created_patient_appears_in_the_listing(client):
    client.post("/api/v1/patients", json=NEW_PATIENT)

    names = [patient["fullName"] for patient in client.get("/api/v1/patients").json()]
    assert "Sofia Herrera Luna" in names


def test_a_future_birth_date_returns_422(client):
    response = client.post("/api/v1/patients", json={**NEW_PATIENT, "birthDate": "2027-01-01"})

    assert response.status_code == 422


def test_the_birth_date_error_follows_the_error_contract(client):
    body = client.post("/api/v1/patients", json={**NEW_PATIENT, "birthDate": "2027-01-01"}).json()

    assert body["code"] == "INVALID_INPUT"
    assert "futuro" in body["message"]


def test_a_short_name_returns_422(client):
    response = client.post("/api/v1/patients", json={**NEW_PATIENT, "fullName": "Al"})

    assert response.status_code == 422


def test_a_malformed_phone_returns_422(client):
    response = client.post("/api/v1/patients", json={**NEW_PATIENT, "phone": "123"})

    assert response.status_code == 422


def test_updating_a_patient_returns_the_new_name(client):
    response = client.patch("/api/v1/patients/1", json={"fullName": "Ana Maria Lopez Garza"})

    assert response.json()["fullName"] == "Ana Maria Lopez Garza"


def test_updating_a_patient_keeps_the_untouched_fields(client):
    before = client.get("/api/v1/patients/1").json()

    after = client.patch("/api/v1/patients/1", json={"fullName": "Ana Maria Lopez Garza"}).json()

    assert after["birthDate"] == before["birthDate"]
    assert after["phone"] == before["phone"]


def test_an_explicit_null_phone_clears_it(client):
    after = client.patch("/api/v1/patients/1", json={"phone": None}).json()

    assert after["phone"] is None


def test_the_patient_update_persists(client):
    client.patch("/api/v1/patients/1", json={"fullName": "Ana Maria Lopez Garza"})

    assert client.get("/api/v1/patients/1").json()["fullName"] == "Ana Maria Lopez Garza"


def test_updating_an_unknown_patient_returns_404(client):
    response = client.patch("/api/v1/patients/999", json={"fullName": "Nadie Aqui"})

    assert response.status_code == 404


def test_deleting_a_patient_returns_204(client):
    response = client.delete("/api/v1/patients/3")

    assert response.status_code == 204


def test_a_deleted_patient_is_gone(client):
    client.delete("/api/v1/patients/3")

    assert client.get("/api/v1/patients/3").status_code == 404


def test_deleting_an_unknown_patient_returns_404(client):
    assert client.delete("/api/v1/patients/999").status_code == 404


def test_a_patient_with_a_live_appointment_cannot_be_deleted(client):
    client.post("/api/v1/appointments", json=APPOINTMENT)

    response = client.delete("/api/v1/patients/1")

    assert response.status_code == 409


def test_the_patient_conflict_explains_how_to_proceed(client):
    client.post("/api/v1/appointments", json=APPOINTMENT)

    body = client.delete("/api/v1/patients/1").json()

    assert "cancelelas" in body["message"]


def test_cancelling_the_appointment_unblocks_the_deletion(client):
    appointment_id = client.post("/api/v1/appointments", json=APPOINTMENT).json()["id"]
    client.put(f"/api/v1/appointments/{appointment_id}/cancellation")

    assert client.delete("/api/v1/patients/1").status_code == 204


# --- Doctores --------------------------------------------------------------


def test_creating_a_doctor_returns_201(client):
    response = client.post("/api/v1/doctors", json=NEW_DOCTOR)

    assert response.status_code == 201


def test_the_created_doctor_prefixes_the_title(client):
    body = client.post("/api/v1/doctors", json=NEW_DOCTOR).json()

    assert body["displayName"] == "Dr(a). Javier Mendoza"


def test_a_created_doctor_persists_across_requests(client):
    created_id = client.post("/api/v1/doctors", json=NEW_DOCTOR).json()["id"]

    assert client.get(f"/api/v1/doctors/{created_id}").json()["speciality"] == "Dermatologia"


def test_a_malformed_license_returns_422(client):
    response = client.post(
        "/api/v1/doctors", json={**NEW_DOCTOR, "medicalLicenseNumber": "ABC-123"}
    )

    assert response.status_code == 422


def test_a_doctor_can_be_created_without_a_license(client):
    payload = {"fullName": "Javier Mendoza", "speciality": "Dermatologia"}

    assert client.post("/api/v1/doctors", json=payload).status_code == 201


def test_updating_a_doctor_returns_the_new_speciality(client):
    response = client.patch("/api/v1/doctors/1", json={"speciality": "Cardiologia Pediatrica"})

    assert response.json()["speciality"] == "Cardiologia Pediatrica"


def test_updating_a_doctor_keeps_the_untouched_fields(client):
    after = client.patch("/api/v1/doctors/1", json={"speciality": "Cardiologia Pediatrica"}).json()

    assert after["fullName"] == "Elena Navarro"


def test_updating_an_unknown_doctor_returns_404(client):
    assert client.patch("/api/v1/doctors/999", json={"speciality": "Pediatria"}).status_code == 404


def test_deleting_a_doctor_returns_204(client):
    assert client.delete("/api/v1/doctors/2").status_code == 204


def test_a_deleted_doctor_is_gone(client):
    client.delete("/api/v1/doctors/2")

    assert client.get("/api/v1/doctors/2").status_code == 404


def test_a_doctor_with_a_live_appointment_cannot_be_deleted(client):
    client.post("/api/v1/appointments", json=APPOINTMENT)

    assert client.delete("/api/v1/doctors/1").status_code == 409


def test_the_deleted_doctor_disappears_from_the_listing(client):
    client.delete("/api/v1/doctors/2")

    names = [doctor["fullName"] for doctor in client.get("/api/v1/doctors").json()]
    assert "Roberto Diaz" not in names


# --- Validaciones de entrada ------------------------------------------------


def test_letters_in_the_phone_are_rejected(client):
    # Regresion: "8112345678abc" perdia las letras en silencio y devolvia 201.
    response = client.post("/api/v1/patients", json={**NEW_PATIENT, "phone": "8112345678abc"})

    assert response.status_code == 422


def test_a_name_with_digits_is_rejected(client):
    response = client.post("/api/v1/patients", json={**NEW_PATIENT, "fullName": "Ana123"})

    assert response.status_code == 422


def test_a_name_of_only_symbols_is_rejected(client):
    response = client.post("/api/v1/patients", json={**NEW_PATIENT, "fullName": "!!!@@@###"})

    assert response.status_code == 422


def test_an_html_tag_is_rejected_as_a_name(client):
    response = client.post(
        "/api/v1/patients", json={**NEW_PATIENT, "fullName": "<script>alert</script>"}
    )

    assert response.status_code == 422


def test_a_phone_with_too_many_digits_is_rejected(client):
    response = client.post("/api/v1/patients", json={**NEW_PATIENT, "phone": "81123456789012345"})

    assert response.status_code == 422


def test_human_separators_in_the_phone_are_accepted(client):
    response = client.post("/api/v1/patients", json={**NEW_PATIENT, "phone": "(81) 1234-5678"})

    assert response.status_code == 201


def test_a_speciality_of_only_digits_is_rejected(client):
    response = client.post("/api/v1/doctors", json={**NEW_DOCTOR, "speciality": "99999"})

    assert response.status_code == 422


def test_a_doctor_name_with_digits_is_rejected(client):
    response = client.post("/api/v1/doctors", json={**NEW_DOCTOR, "fullName": "666666"})

    assert response.status_code == 422
