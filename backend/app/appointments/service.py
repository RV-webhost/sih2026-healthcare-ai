import uuid
from datetime import datetime, date, time, timezone
from typing import Optional, Tuple, List, Dict, Any

from app.extensions import db
from app.models import Appointment


def check_doctor_availability_stub(
    doctor_id: uuid.UUID,
    appointment_date: date,
    appointment_time: time
) -> bool:
    """
    Mock / Stub function for Member 3 Doctor Availability module.
    Always returns True to represent doctor availability.
    """
    return True


def create_appointment(
    patient_id: Any,
    doctor_id: Any,
    appointment_date: date,
    appointment_time: time,
    reason: Optional[str] = None,
    status: str = "CONFIRMED"
) -> Tuple[Optional[Appointment], str, Optional[str]]:
    """
    Creates a new appointment after verifying doctor availability and slot uniqueness.

    Returns:
        (appointment_instance, message, error_code)
    """
    # Normalize UUIDs
    try:
        p_uuid = uuid.UUID(str(patient_id)) if not isinstance(patient_id, uuid.UUID) else patient_id
        d_uuid = uuid.UUID(str(doctor_id)) if not isinstance(doctor_id, uuid.UUID) else doctor_id
    except (ValueError, TypeError):
        return None, "Invalid patient_id or doctor_id UUID format.", "INVALID_ID"

    # Step 1: Check Member 3 Doctor Availability Stub
    if not check_doctor_availability_stub(d_uuid, appointment_date, appointment_time):
        return None, "Doctor is not available at the requested date and time.", "DOCTOR_UNAVAILABLE"

    # Step 2: Query DB to ensure the specific slot is not already booked
    existing_slot = Appointment.query.filter(
        Appointment.doctor_id == d_uuid,
        Appointment.appointment_date == appointment_date,
        Appointment.appointment_time == appointment_time,
        Appointment.status != "CANCELLED"
    ).first()

    if existing_slot:
        return None, "The requested doctor appointment slot is already booked.", "SLOT_UNAVAILABLE"

    # Step 3: Create and commit the appointment
    try:
        appointment = Appointment(
            patient_id=p_uuid,
            doctor_id=d_uuid,
            appointment_date=appointment_date,
            appointment_time=appointment_time,
            status=status,
            reason=reason
        )
        db.session.add(appointment)
        db.session.commit()
        return appointment, "Appointment booked successfully.", None
    except Exception as e:
        db.session.rollback()
        return None, f"Database error creating appointment: {str(e)}", "DATABASE_ERROR"


def get_appointment_by_id(appointment_id: Any) -> Tuple[Optional[Appointment], str, Optional[str]]:
    """
    Retrieves an appointment by its UUID.
    """
    try:
        a_uuid = uuid.UUID(str(appointment_id)) if not isinstance(appointment_id, uuid.UUID) else appointment_id
    except (ValueError, TypeError):
        return None, "Invalid appointment ID format.", "INVALID_ID"

    appointment = db.session.get(Appointment, a_uuid)
    if not appointment:
        return None, "Appointment not found.", "APPOINTMENT_NOT_FOUND"

    return appointment, "Appointment retrieved successfully.", None


def list_patient_appointments(patient_id: Any) -> Tuple[Optional[List[Appointment]], str, Optional[str]]:
    """
    Lists all appointments for a specific patient.
    """
    try:
        p_uuid = uuid.UUID(str(patient_id)) if not isinstance(patient_id, uuid.UUID) else patient_id
    except (ValueError, TypeError):
        return None, "Invalid patient ID format.", "INVALID_ID"

    appointments = Appointment.query.filter_by(patient_id=p_uuid).order_by(
        Appointment.appointment_date.desc(),
        Appointment.appointment_time.desc()
    ).all()

    return appointments, "Patient appointments retrieved successfully.", None


def cancel_appointment(appointment_id: Any) -> Tuple[Optional[Appointment], str, Optional[str]]:
    """
    Cancels an existing appointment.
    """
    try:
        a_uuid = uuid.UUID(str(appointment_id)) if not isinstance(appointment_id, uuid.UUID) else appointment_id
    except (ValueError, TypeError):
        return None, "Invalid appointment ID format.", "INVALID_ID"

    appointment = db.session.get(Appointment, a_uuid)
    if not appointment:
        return None, "Appointment not found.", "APPOINTMENT_NOT_FOUND"

    if appointment.status == "CANCELLED":
        return appointment, "Appointment is already cancelled.", None

    try:
        appointment.status = "CANCELLED"
        appointment.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        return appointment, "Appointment cancelled successfully.", None
    except Exception as e:
        db.session.rollback()
        return None, f"Database error cancelling appointment: {str(e)}", "DATABASE_ERROR"


def reschedule_appointment(
    appointment_id: Any,
    new_date: date,
    new_time: time
) -> Tuple[Optional[Appointment], str, Optional[str]]:
    """
    Reschedules an existing appointment to a new date and time slot after checking availability.
    """
    try:
        a_uuid = uuid.UUID(str(appointment_id)) if not isinstance(appointment_id, uuid.UUID) else appointment_id
    except (ValueError, TypeError):
        return None, "Invalid appointment ID format.", "INVALID_ID"

    appointment = db.session.get(Appointment, a_uuid)
    if not appointment:
        return None, "Appointment not found.", "APPOINTMENT_NOT_FOUND"

    if appointment.status == "CANCELLED":
        return None, "Cannot reschedule a cancelled appointment.", "INVALID_STATUS"

    # Step 1: Check Doctor Availability Stub
    if not check_doctor_availability_stub(appointment.doctor_id, new_date, new_time):
        return None, "Doctor is not available at the new requested slot.", "DOCTOR_UNAVAILABLE"

    # Step 2: Check for conflicting booking in the new slot
    existing_slot = Appointment.query.filter(
        Appointment.doctor_id == appointment.doctor_id,
        Appointment.appointment_date == new_date,
        Appointment.appointment_time == new_time,
        Appointment.status != "CANCELLED",
        Appointment.id != appointment.id
    ).first()

    if existing_slot:
        return None, "The requested doctor appointment slot is already booked.", "SLOT_UNAVAILABLE"

    # Step 3: Update appointment slot
    try:
        appointment.appointment_date = new_date
        appointment.appointment_time = new_time
        appointment.status = "CONFIRMED"
        appointment.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        return appointment, "Appointment rescheduled successfully.", None
    except Exception as e:
        db.session.rollback()
        return None, f"Database error rescheduling appointment: {str(e)}", "DATABASE_ERROR"
