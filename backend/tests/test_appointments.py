import uuid
from datetime import date, time, timedelta


def test_create_appointment_success(client, mock_patient_id, mock_doctor_id):
    """Test creating a valid appointment successfully."""
    payload = {
        "patient_id": str(mock_patient_id),
        "doctor_id": str(mock_doctor_id),
        "date": "2026-09-10",
        "time": "09:30:00",
        "reason": "Annual Wellness Exam"
    }
    response = client.post("/api/v1/appointments", json=payload)
    assert response.status_code == 201

    json_data = response.get_json()
    assert json_data["success"] is True
    assert json_data["error_code"] is None
    assert json_data["data"]["patient_id"] == str(mock_patient_id)
    assert json_data["data"]["doctor_id"] == str(mock_doctor_id)
    assert json_data["data"]["appointment_date"] == "2026-09-10"
    assert json_data["data"]["appointment_time"] == "09:30:00"
    assert json_data["data"]["status"] == "CONFIRMED"


def test_create_appointment_duplicate_slot(client, mock_patient_id, mock_doctor_id):
    """Test that duplicate doctor/date/time booking is rejected with SLOT_UNAVAILABLE."""
    payload1 = {
        "patient_id": str(mock_patient_id),
        "doctor_id": str(mock_doctor_id),
        "date": "2026-09-12",
        "time": "14:00:00",
        "reason": "First Booking"
    }
    res1 = client.post("/api/v1/appointments", json=payload1)
    assert res1.status_code == 201

    # Second patient tries to book the exact same slot with the same doctor
    payload2 = {
        "patient_id": str(uuid.uuid4()),
        "doctor_id": str(mock_doctor_id),
        "date": "2026-09-12",
        "time": "14:00:00",
        "reason": "Conflicting Booking"
    }
    res2 = client.post("/api/v1/appointments", json=payload2)
    assert res2.status_code == 409

    json_data = res2.get_json()
    assert json_data["success"] is False
    assert json_data["error_code"] == "SLOT_UNAVAILABLE"
    assert "already booked" in json_data["message"]


def test_create_appointment_invalid_uuid(client):
    """Test that invalid UUIDs for patient or doctor are rejected with 400."""
    payload = {
        "patient_id": "not-a-valid-uuid",
        "doctor_id": str(uuid.uuid4()),
        "date": "2026-09-15",
        "time": "10:00:00"
    }
    response = client.post("/api/v1/appointments", json=payload)
    assert response.status_code == 400

    json_data = response.get_json()
    assert json_data["success"] is False
    assert json_data["error_code"] == "VALIDATION_ERROR"


def test_cancel_appointment(client, mock_patient_id, mock_doctor_id):
    """Test cancelling an appointment updates status to CANCELLED."""
    payload = {
        "patient_id": str(mock_patient_id),
        "doctor_id": str(mock_doctor_id),
        "date": "2026-09-18",
        "time": "11:00:00"
    }
    create_res = client.post("/api/v1/appointments", json=payload)
    assert create_res.status_code == 201
    appt_id = create_res.get_json()["data"]["id"]

    cancel_res = client.patch(f"/api/v1/appointments/{appt_id}/cancel")
    assert cancel_res.status_code == 200

    json_data = cancel_res.get_json()
    assert json_data["success"] is True
    assert json_data["data"]["status"] == "CANCELLED"

    # Verify via GET endpoint
    get_res = client.get(f"/api/v1/appointments/{appt_id}")
    assert get_res.status_code == 200
    assert get_res.get_json()["data"]["status"] == "CANCELLED"


def test_reschedule_appointment(client, mock_patient_id, mock_doctor_id):
    """Test rescheduling checks slot availability and updates the appointment slot."""
    # Create original appointment
    create_res = client.post("/api/v1/appointments", json={
        "patient_id": str(mock_patient_id),
        "doctor_id": str(mock_doctor_id),
        "date": "2026-09-22",
        "time": "10:00:00"
    })
    assert create_res.status_code == 201
    appt_id = create_res.get_json()["data"]["id"]

    # Create another booking on target date/time to test conflict
    conflict_res = client.post("/api/v1/appointments", json={
        "patient_id": str(uuid.uuid4()),
        "doctor_id": str(mock_doctor_id),
        "date": "2026-09-25",
        "time": "15:00:00"
    })
    assert conflict_res.status_code == 201

    # Try rescheduling to the taken slot -> should fail with 409
    resched_fail = client.patch(f"/api/v1/appointments/{appt_id}/reschedule", json={
        "date": "2026-09-25",
        "time": "15:00:00"
    })
    assert resched_fail.status_code == 409
    assert resched_fail.get_json()["error_code"] == "SLOT_UNAVAILABLE"

    # Reschedule to an open slot -> should succeed with 200
    resched_ok = client.patch(f"/api/v1/appointments/{appt_id}/reschedule", json={
        "date": "2026-09-26",
        "time": "16:00:00"
    })
    assert resched_ok.status_code == 200
    json_data = resched_ok.get_json()
    assert json_data["success"] is True
    assert json_data["data"]["appointment_date"] == "2026-09-26"
    assert json_data["data"]["appointment_time"] == "16:00:00"


def test_list_patient_appointments(client, mock_patient_id, mock_doctor_id):
    """Test listing appointments for a patient."""
    client.post("/api/v1/appointments", json={
        "patient_id": str(mock_patient_id),
        "doctor_id": str(mock_doctor_id),
        "date": "2026-10-01",
        "time": "09:00:00"
    })
    client.post("/api/v1/appointments", json={
        "patient_id": str(mock_patient_id),
        "doctor_id": str(mock_doctor_id),
        "date": "2026-10-02",
        "time": "10:00:00"
    })

    response = client.get(f"/api/v1/appointments/patient/{mock_patient_id}")
    assert response.status_code == 200
    data = response.get_json()["data"]
    assert len(data) == 2


def test_get_appointment_not_found(client):
    """Test querying non-existent appointment returns 404."""
    response = client.get(f"/api/v1/appointments/{uuid.uuid4()}")
    assert response.status_code == 404
    assert response.get_json()["error_code"] == "APPOINTMENT_NOT_FOUND"
