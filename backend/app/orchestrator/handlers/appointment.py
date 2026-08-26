"""
M6 appointment workflow coordinator.

This module only sequences calls to M3 (doctors), M2 (appointments),
and M4 (tokens).

It does not query the database or calculate slots directly.
"""

from datetime import datetime

from app.orchestrator.schemas import (
    build_success_response,
    build_error_response,
)

BOOK_INTENT = "BOOK_APPOINTMENT"


# ---------------------------------------------------------------------------
# M3 — Doctor availability
# ---------------------------------------------------------------------------

def _m3_get_doctor_availability(
    specialization: str,
    date: str,
) -> dict:
    """Use the real M3 doctor-search and availability services."""

    from app.doctors.service import (
        calculate_availability,
        get_doctors,
    )

    check_date = datetime.strptime(date, "%Y-%m-%d").date()

    doctors = get_doctors(specialization=specialization)

    available_doctors = []

    for doctor in doctors:
        doctor_id = str(doctor.id)

        availability_response = calculate_availability(
            doctor_id=doctor_id,
            check_date=check_date,
        )

        if not availability_response.get("success"):
            continue

        availability_data = availability_response.get("data") or {}
        raw_slots = availability_data.get("slots") or []

        available_slots = []

        for slot in raw_slots:
            if isinstance(slot, dict):
                if slot.get("available"):
                    available_slots.append(
                        slot.get("time") or slot.get("slot")
                    )
            elif isinstance(slot, str):
                available_slots.append(slot)

        available_slots = [
            slot for slot in available_slots if slot
        ]

        if available_slots:
            available_doctors.append(
                {
                    "doctor_id": doctor_id,
                    "doctor_name": doctor.name,
                    "specialization": doctor.specialization,
                    "available_slots": available_slots,
                }
            )

    return {
        "specialization": specialization,
        "date": date,
        "doctors": available_doctors,
    }


# ---------------------------------------------------------------------------
# M2 — Appointment creation
# ---------------------------------------------------------------------------

def _m2_create_appointment(
    doctor_id: str,
    patient_id: str,
    date: str,
    time: str,
) -> dict | None:
    """
    Call the real M2 appointment service.

    M2 returns:
        (appointment, message, error_code)

    This adapter converts that into the dictionary expected by M6.
    """

    try:
        from app.appointments.service import create_appointment

        appointment_date = datetime.strptime(
            date,
            "%Y-%m-%d",
        ).date()

        appointment_time = datetime.strptime(
            time,
            "%H:%M",
        ).time()

        appointment, message, error_code = create_appointment(
            patient_id=patient_id,
            doctor_id=doctor_id,
            appointment_date=appointment_date,
            appointment_time=appointment_time,
        )

        if error_code or appointment is None:
            return None

        return {
            "appointment_id": str(appointment.id),
            "doctor_id": str(appointment.doctor_id),
            "patient_id": str(appointment.patient_id),
            "date": appointment.appointment_date.isoformat(),
            "time": appointment.appointment_time.strftime("%H:%M"),
            "status": appointment.status,
        }

    except (
        ImportError,
        AttributeError,
        TypeError,
        ValueError,
    ):
        return None


# ---------------------------------------------------------------------------
# M4 — OPD token generation
# ---------------------------------------------------------------------------

def _m4_generate_opd_token(
    appointment_id: str,
    patient_id: str,
) -> dict | None:
    """Call the real M4 token service and normalize its Token response."""
    try:
        from app.extensions import db
        from app.tokens.service import create_token

        token = create_token(
            db.session,
            patient_id=patient_id,
            appointment_id=appointment_id,
        )

        return {
            "token_id": str(token.id),
            "appointment_id": str(token.appointment_id),
            "token_number": token.token_number,
            "patient_id": str(token.patient_id),
            "doctor_id": str(token.doctor_id),
            "status": (
                token.status.value
                if hasattr(token.status, "value")
                else str(token.status)
            ),
        }

    except Exception as e:
        import traceback

        print("\n========== M4 TOKEN ERROR ==========")
        print(f"{type(e).__name__}: {e}")
        traceback.print_exc()
        print("====================================\n")

        return None
# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _has_slots(availability: dict) -> bool:
    """Return True if at least one doctor has at least one available slot."""

    if not availability:
        return False

    doctors = (
        availability.get("doctors")
        or availability.get("available_doctors")
        or []
    )

    if not doctors:
        slots = (
            availability.get("slots")
            or availability.get("available_slots")
            or []
        )
        return bool(slots)

    for doctor in doctors:
        slots = (
            doctor.get("available_slots")
            or doctor.get("slots")
            or []
        )

        if slots:
            return True

    return False


# ---------------------------------------------------------------------------
# Appointment handler
# ---------------------------------------------------------------------------

class AppointmentHandler:
    """
    Coordinates BOOK_APPOINTMENT:

    collect information
        →
    M3 availability
        →
    M2 appointment booking
        →
    M4 OPD token
    """

    @staticmethod
    def handle_booking(
        entities: dict,
        user: dict,
    ) -> dict:

        entities = entities or {}
        user = user or {}

        specialization = entities.get("specialization")
        appointment_date = entities.get("date")

        # M1 may provide the requested slot under different field names.
        preference = (
            entities.get("preference")
            or entities.get("time")
            or entities.get("time_preference")
        )

        # ---------------------------------------------------------------
        # Missing specialization
        # ---------------------------------------------------------------

        if not specialization:
            return build_success_response(
                intent=BOOK_INTENT,
                message=(
                    "Which department or specialization do you need? "
                    "For example, Cardiology."
                ),
                data={
                    "missing_field": "specialization",
                },
                next_action="ASK_SPECIALIZATION",
            )

        # ---------------------------------------------------------------
        # Missing date
        # ---------------------------------------------------------------

        if not appointment_date:
            return build_success_response(
                intent=BOOK_INTENT,
                message="What date would you like the appointment?",
                data={
                    "specialization": specialization,
                    "missing_field": "date",
                },
                next_action="ASK_DATE",
            )

        # ---------------------------------------------------------------
        # M3 — Find doctors and available slots
        # ---------------------------------------------------------------

        availability = _m3_get_doctor_availability(
            specialization,
            appointment_date,
        )

        if not _has_slots(availability):
            return build_error_response(
                intent=BOOK_INTENT,
                message=(
                    f"No doctors or slots are available for "
                    f"{specialization} on {appointment_date}."
                ),
                error_code="NO_SLOTS_AVAILABLE",
                next_action="CLARIFY",
            )

        doctors = (
            availability.get("doctors")
            or availability.get("available_doctors")
            or []
        )

        # ---------------------------------------------------------------
        # No slot selected — return available options
        # ---------------------------------------------------------------

        if not preference:
            return build_success_response(
                intent=BOOK_INTENT,
                message=(
                    f"Here are the available slots for "
                    f"{specialization} on {appointment_date}. "
                    "Please choose a time."
                ),
                data={
                    "specialization": specialization,
                    "date": appointment_date,
                    "available_doctors": doctors,
                    "availability": availability,
                },
                next_action="SELECT_APPOINTMENT_SLOT",
            )

        # ---------------------------------------------------------------
        # M2 — Create appointment
        # ---------------------------------------------------------------

        first_doctor = doctors[0] if doctors else {}

        doctor_id = (
            entities.get("doctor_id")
            or first_doctor.get("doctor_id")
            or first_doctor.get("id")
        )

        patient_id = (
            user.get("patient_id")
            or user.get("id")
            or user.get("user_id")
        )

        appointment = _m2_create_appointment(
            doctor_id=doctor_id,
            patient_id=patient_id,
            date=appointment_date,
            time=preference,
        )

        if not appointment or not appointment.get("appointment_id"):
            return build_error_response(
                intent=BOOK_INTENT,
                message=(
                    "We could not book that appointment. "
                    "Please try another slot."
                ),
                error_code="BOOKING_FAILED",
                next_action="SELECT_APPOINTMENT_SLOT",
            )

        # ---------------------------------------------------------------
        # M4 — Generate OPD token
        # ---------------------------------------------------------------

        token = _m4_generate_opd_token(
            appointment_id=appointment["appointment_id"],
            patient_id=patient_id,
        )

        if not token:
            return build_error_response(
                intent=BOOK_INTENT,
                message=(
                    "Your appointment was booked, but we could not "
                    "generate an OPD token."
                ),
                error_code="TOKEN_GENERATION_FAILED",
                next_action="RETRY",
            )

        # ---------------------------------------------------------------
        # Final success response
        # ---------------------------------------------------------------

        return build_success_response(
            intent=BOOK_INTENT,
            message=(
                "Your appointment is booked and an OPD token "
                "has been generated."
            ),
            data={
                "appointment": appointment,
                "token": token,
                "token_number": token["token_number"],
            },
        )