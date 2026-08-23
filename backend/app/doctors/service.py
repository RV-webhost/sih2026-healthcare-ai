import uuid
from datetime import date, time, datetime
from typing import List, Optional, Dict, Any
from app.extensions import db
from app.doctors.models import Doctor, DoctorSchedule, DoctorLeave
from app.doctors.schemas import (
    standard_response,
    format_doctor_out,
    format_doctor_schedule_out,
    format_doctor_availability_out,
    format_slot_out,
)


def _normalize_time_str(t_str: str) -> str:
    """Normalize time string HH:MM:SS or HH:MM to HH:MM format."""
    parts = str(t_str).strip().split(":")
    if len(parts) >= 2:
        return f"{int(parts[0]):02d}:{int(parts[1]):02d}"
    return str(t_str)


def get_doctors(department: Optional[str] = None, specialization: Optional[str] = None) -> List[Doctor]:
    """Query doctors using Flask-SQLAlchemy db.session, optionally filtered by department."""
    query = Doctor.query
    if hasattr(Doctor, "is_available"):
        query = query.filter(Doctor.is_available.is_(True))

    dept_filter = department or specialization
    if dept_filter:
        query = query.filter(Doctor.department.ilike(f"%{dept_filter.strip()}%"))
    return query.all()


def get_doctor_by_id(doctor_id: str) -> Optional[Doctor]:
    """Fetch doctor details by doctor_id string/UUID."""
    if not doctor_id:
        return None
    return Doctor.query.filter(Doctor.doctor_id == str(doctor_id).strip()).first()


def get_doctor_schedule(doctor_id: str) -> List[Dict[str, Any]]:
    """Fetch all regular schedules for the doctor with formatted times (HH:MM)."""
    if not doctor_id:
        return []
    schedules = DoctorSchedule.query.filter(DoctorSchedule.doctor_id == str(doctor_id).strip()).all()
    return [format_doctor_schedule_out(s) for s in schedules]


def calculate_availability(
    doctor_id: str,
    check_date: date,
    booked_slots: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Calculate doctor slot availability for a specific date considering leaves,
    regular schedules, and existing booked slots using Flask-SQLAlchemy db.session.
    """
    if not doctor_id:
        return standard_response(
            success=False,
            data=None,
            message="Doctor ID is required",
            error_code="DOCTOR_NOT_FOUND",
        )

    # Step 1: Validate doctor exists and is available
    doctor = Doctor.query.filter(Doctor.doctor_id == str(doctor_id).strip()).first()
    if not doctor:
        return standard_response(
            success=False,
            data=None,
            message="Doctor not found",
            error_code="DOCTOR_NOT_FOUND",
        )
    if hasattr(doctor, "is_available") and not doctor.is_available:
        return standard_response(
            success=False,
            data=None,
            message="Doctor is unavailable",
            error_code="DOCTOR_INACTIVE",
        )

    # Step 2: Check doctor_leaves for check_date
    leave = DoctorLeave.query.filter(
        DoctorLeave.doctor_id == str(doctor.doctor_id),
        DoctorLeave.leave_date == check_date
    ).first()

    if leave:
        reason_msg = f"Doctor is on leave: {leave.reason}" if leave.reason else "Doctor is on leave"
        avail_data = format_doctor_availability_out(
            doctor_id=str(doctor.doctor_id),
            check_date=check_date,
            available=False,
            slots=[]
        )
        return standard_response(
            success=True,
            data=avail_data,
            message=reason_msg,
            error_code="DOCTOR_ON_LEAVE",
        )

    # Step 3: Check regular schedule for the day of the week
    day_name = check_date.strftime("%A")
    schedules = DoctorSchedule.query.filter(
        DoctorSchedule.doctor_id == str(doctor.doctor_id),
        DoctorSchedule.day_of_week.ilike(day_name)
    ).all()

    if not schedules:
        avail_data = format_doctor_availability_out(
            doctor_id=str(doctor.doctor_id),
            check_date=check_date,
            available=False,
            slots=[]
        )
        return standard_response(
            success=True,
            data=avail_data,
            message=f"No regular schedule configured for {day_name}",
            error_code=None,
        )

    # Step 4 & Step 5: Generate 30-minute time slots and compare with booked_slots
    normalized_booked = {_normalize_time_str(s) for s in (booked_slots or [])}
    slots = []

    for schedule in schedules:
        start_t = schedule.start_time
        end_t = schedule.end_time
        duration = schedule.slot_duration or 30

        current_mins = start_t.hour * 60 + start_t.minute
        end_mins = end_t.hour * 60 + end_t.minute

        while current_mins + duration <= end_mins:
            h = current_mins // 60
            m = current_mins % 60
            slot_str = f"{h:02d}:{m:02d}"

            is_available = slot_str not in normalized_booked
            slots.append(format_slot_out(time_str=slot_str, available=is_available))
            current_mins += duration

    # Step 6: Overall availability is True if at least one slot is free
    overall_available = any(s["available"] for s in slots) if slots else False
    avail_data = format_doctor_availability_out(
        doctor_id=str(doctor.doctor_id),
        check_date=check_date,
        available=overall_available,
        slots=slots
    )

    return standard_response(
        success=True,
        data=avail_data,
        message="Doctor availability calculated successfully",
        error_code=None,
    )


def create_doctor(doctor_data: Dict[str, Any]) -> Doctor:
    """Helper to create a new doctor entry using Flask-SQLAlchemy db.session."""
    data = dict(doctor_data)
    if "id" in data and "doctor_id" not in data:
        data["doctor_id"] = str(data.pop("id"))
    elif "doctor_id" in data and isinstance(data["doctor_id"], uuid.UUID):
        data["doctor_id"] = str(data["doctor_id"])
    doctor = Doctor(**data)
    db.session.add(doctor)
    db.session.commit()
    return doctor


def create_doctor_schedule(schedule_data: Dict[str, Any]) -> DoctorSchedule:
    """Helper to create a doctor schedule entry using Flask-SQLAlchemy db.session."""
    data = dict(schedule_data)
    if "id" in data and isinstance(data["id"], uuid.UUID):
        data["id"] = str(data["id"])
    if "doctor_id" in data and isinstance(data["doctor_id"], uuid.UUID):
        data["doctor_id"] = str(data["doctor_id"])
    schedule = DoctorSchedule(**data)
    db.session.add(schedule)
    db.session.commit()
    return schedule


def create_doctor_leave(leave_data: Dict[str, Any]) -> DoctorLeave:
    """Helper to create a doctor leave entry using Flask-SQLAlchemy db.session."""
    data = dict(leave_data)
    if "id" in data and isinstance(data["id"], uuid.UUID):
        data["id"] = str(data["id"])
    if "doctor_id" in data and isinstance(data["doctor_id"], uuid.UUID):
        data["doctor_id"] = str(data["doctor_id"])
    leave = DoctorLeave(**data)
    db.session.add(leave)
    db.session.commit()
    return leave
