"""
M6 appointment workflow coordinator.

This module only sequences calls to M3 (doctors), M2 (appointments), and M4 (tokens).
It does not query the database or calculate slots.
"""

from app.orchestrator.schemas import build_success_response, build_error_response

BOOK_INTENT = "BOOK_APPOINTMENT"


# ---------------------------------------------------------------------------
# Mocked downstream service calls (stand-ins for M3 / M2 / M4)
# ---------------------------------------------------------------------------

def _m3_get_doctor_availability(specialization: str, date: str) -> dict:
    """Mocked call to app.doctors.service.get_doctor_availability(specialization, date)."""
    try:
        from app.doctors.service import get_doctor_availability

        return get_doctor_availability(specialization, date)
    except (ImportError, AttributeError):
        return {
            "specialization": specialization,
            "date": date,
            "doctors": [
                {
                    "doctor_id": "D204",
                    "doctor_name": "Dr. Sharma",
                    "specialization": specialization,
                    "available_slots": ["09:00", "10:30", "15:00"],
                }
            ],
        }


def _m2_create_appointment(doctor_id: str, patient_id: str, date: str, time: str) -> dict:
    """Mocked call to app.appointments.service.create_appointment(...)."""
    try:
        from app.appointments.service import create_appointment

        return create_appointment(doctor_id, patient_id, date, time)
    except (ImportError, AttributeError):
        return {
            "appointment_id": "APT-1001",
            "doctor_id": doctor_id,
            "patient_id": patient_id,
            "date": date,
            "time": time,
            "status": "CONFIRMED",
        }


def _m4_generate_opd_token(appointment_id: str) -> dict:
    """Mocked call to app.tokens.service.generate_opd_token(appointment_id)."""
    try:
        from app.tokens.service import generate_opd_token

        return generate_opd_token(appointment_id)
    except (ImportError, AttributeError):
        return {
            "token_id": "TOK-1001",
            "appointment_id": appointment_id,
            "token_number": 12,
            "status": "WAITING",
        }


def _has_slots(availability: dict) -> bool:
    """True if M3 returned at least one doctor with at least one slot."""
    if not availability:
        return False
    doctors = availability.get("doctors") or availability.get("available_doctors") or []
    if not doctors:
        slots = availability.get("slots") or availability.get("available_slots") or []
        return bool(slots)
    for doctor in doctors:
        slots = doctor.get("available_slots") or doctor.get("slots") or []
        if slots:
            return True
    return False


class AppointmentHandler:
    """Coordinates BOOK_APPOINTMENT: collect info → M3 availability → M2 book → M4 token."""

    @staticmethod
    def handle_booking(entities: dict, user: dict) -> dict:
        entities = entities or {}
        user = user or {}

        specialization = entities.get("specialization")
        date = entities.get("date")
        # M1 may label the time slot as preference, time, or time_preference
        preference = (
            entities.get("preference")
            or entities.get("time")
            or entities.get("time_preference")
        )

        # --- Missing info: ask one thing at a time (specialization first, then date) ---
        if not specialization:
            return build_success_response(
                intent=BOOK_INTENT,
                message="Which department or specialization do you need? For example, Cardiology.",
                data={"missing_field": "specialization"},
                next_action="ASK_SPECIALIZATION",
            )

        if not date:
            return build_success_response(
                intent=BOOK_INTENT,
                message="What date would you like the appointment?",
                data={"specialization": specialization, "missing_field": "date"},
                next_action="ASK_DATE",
            )

        # --- M3: doctor / slot availability ---
        availability = _m3_get_doctor_availability(specialization, date)
        if not _has_slots(availability):
            return build_error_response(
                intent=BOOK_INTENT,
                message=f"No doctors or slots are available for {specialization} on {date}.",
                error_code="NO_SLOTS_AVAILABLE",
                next_action="CLARIFY",
            )

        doctors = availability.get("doctors") or availability.get("available_doctors") or []

        # --- No time chosen yet: present slots and wait for the user to pick one ---
        if not preference:
            return build_success_response(
                intent=BOOK_INTENT,
                message=f"Here are the available slots for {specialization} on {date}. Please choose a time.",
                data={
                    "specialization": specialization,
                    "date": date,
                    "available_doctors": doctors,
                    "availability": availability,
                },
                next_action="SELECT_APPOINTMENT_SLOT",
            )

        # --- M2: create the appointment with the chosen slot ---
        first_doctor = doctors[0] if doctors else {}
        doctor_id = (
            entities.get("doctor_id")
            or first_doctor.get("doctor_id")
            or first_doctor.get("id")
        )
        patient_id = user.get("patient_id") or user.get("id") or user.get("user_id")

        appointment = _m2_create_appointment(doctor_id, patient_id, date, preference)
        if not appointment or not appointment.get("appointment_id"):
            return build_error_response(
                intent=BOOK_INTENT,
                message="We could not book that appointment. Please try another slot.",
                error_code="BOOKING_FAILED",
                next_action="SELECT_APPOINTMENT_SLOT",
            )

        # --- M4: generate an OPD token for the confirmed appointment ---
        token = _m4_generate_opd_token(appointment["appointment_id"])

        return build_success_response(
            intent=BOOK_INTENT,
            message="Your appointment is booked and an OPD token has been generated.",
            data={
                "appointment": appointment,
                "token": token,
                "token_number": (token or {}).get("token_number"),
            },
        )
