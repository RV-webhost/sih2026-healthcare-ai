import uuid
import requests
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


def _normalize_time_str(t_str: Any) -> str:
    """Normalize time string HH:MM:SS, HH:MM, or time object to HH:MM format."""
    if isinstance(t_str, time):
        return t_str.strftime("%H:%M")
    parts = str(t_str).strip().split(":")
    if len(parts) >= 2:
        try:
            return f"{int(parts[0]):02d}:{int(parts[1]):02d}"
        except ValueError:
            pass
    return str(t_str).strip()


def _coerce_uuid(val: Any) -> Optional[uuid.UUID]:
    """Helper to coerce a string or UUID into a valid UUID object."""
    if val is None:
        return None
    if isinstance(val, uuid.UUID):
        return val
    try:
        return uuid.UUID(str(val).strip())
    except (ValueError, AttributeError):
        try:
            return uuid.uuid5(uuid.NAMESPACE_DNS, str(val).strip())
        except Exception:
            return None


def get_doctors(department: Optional[str] = None, specialization: Optional[str] = None) -> List[Doctor]:
    """Query doctors using Flask-SQLAlchemy db.session, optionally filtered by department or specialization."""
    query = Doctor.query
    if hasattr(Doctor, "status"):
        query = query.filter(Doctor.status == "ACTIVE")
    elif hasattr(Doctor, "is_available"):
        query = query.filter(Doctor.is_available.is_(True))

    dept_filter = department or specialization
    if dept_filter:
        pattern = f"%{dept_filter.strip()}%"
        query = query.filter(
            (Doctor.department.ilike(pattern)) |
            (Doctor.specialization.ilike(pattern))
        )
    return query.all()


def get_doctor_by_id(doctor_id: str) -> Optional[Doctor]:
    """Fetch doctor details by doctor_id string/UUID."""
    if not doctor_id:
        return None
    doc_uuid = _coerce_uuid(doctor_id)
    if not doc_uuid:
        return None
    return Doctor.query.filter(Doctor.id == doc_uuid).first()


def get_doctor_schedule(doctor_id: str) -> List[Dict[str, Any]]:
    """Fetch all regular schedules for the doctor with formatted times (HH:MM)."""
    if not doctor_id:
        return []
    doc_uuid = _coerce_uuid(doctor_id)
    if not doc_uuid:
        return []
    schedules = DoctorSchedule.query.filter(DoctorSchedule.doctor_id == doc_uuid).all()
    return [format_doctor_schedule_out(s) for s in schedules]


def calculate_availability(
    doctor_id: str,
    check_date: date,
    booked_slots: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Calculate doctor slot availability for a specific date considering leaves,
    regular schedules, and existing booked slots (via M2 HTTP API or parameter)
    using Flask-SQLAlchemy db.session.
    """
    if not doctor_id:
        return standard_response(
            success=False,
            data=None,
            message="Doctor ID is required",
            error_code="DOCTOR_NOT_FOUND",
        )

    # Step 1: Validate doctor exists and is active/available
    doc_uuid = _coerce_uuid(doctor_id)
    doctor = Doctor.query.filter(Doctor.id == doc_uuid).first() if doc_uuid else None
    if not doctor:
        return standard_response(
            success=False,
            data=None,
            message="Doctor not found",
            error_code="DOCTOR_NOT_FOUND",
        )

    if (hasattr(doctor, "status") and doctor.status != "ACTIVE") or (
        hasattr(doctor, "is_available") and not doctor.is_available
    ):
        return standard_response(
            success=False,
            data=None,
            message="Doctor is unavailable",
            error_code="DOCTOR_INACTIVE",
        )

    # Step 2: Check doctor_leaves for check_date
    leave = DoctorLeave.query.filter(
        DoctorLeave.doctor_id == doctor.id,
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
            success=False,
            data=avail_data,
            message=reason_msg,
            error_code="DOCTOR_ON_LEAVE",
        )

    # Step 3: Check regular schedule for the day of the week
    day_name = check_date.strftime("%A")
    schedules = DoctorSchedule.query.filter(
        DoctorSchedule.doctor_id == doctor.id,
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

    # Step 4: Fetch booked slots from M2 Appointments API if not explicitly supplied
    booked_list: List[str] = []
    if booked_slots is not None:
        booked_list = list(booked_slots)
    else:
        try:
            date_str = check_date.strftime("%Y-%m-%d") if isinstance(check_date, (date, datetime)) else str(check_date)
            m2_url = f"http://127.0.0.1:5000/api/v1/appointments/doctor/{doctor_id}?date={date_str}"
            response = requests.get(m2_url, timeout=5)
            if response.status_code == 200:
                resp_json = response.json()
                raw_items = []
                if isinstance(resp_json, dict):
                    data_val = resp_json.get("data")
                    if isinstance(data_val, list):
                        raw_items = data_val
                    elif isinstance(data_val, dict) and "booked_slots" in data_val:
                        raw_items = data_val["booked_slots"]
                    elif "booked_slots" in resp_json:
                        raw_items = resp_json["booked_slots"]
                    elif "appointments" in resp_json:
                        raw_items = resp_json["appointments"]
                elif isinstance(resp_json, list):
                    raw_items = resp_json

                for item in raw_items:
                    if isinstance(item, str):
                        booked_list.append(item)
                    elif isinstance(item, dict):
                        t_val = (
                            item.get("time")
                            or item.get("appointment_time")
                            or item.get("start_time")
                            or item.get("slot_time")
                            or item.get("slot")
                        )
                        if t_val:
                            booked_list.append(str(t_val))
        except Exception:
            booked_list = []

    normalized_booked = {_normalize_time_str(s) for s in booked_list}

    # Step 5: Generate slots and compare with booked slots
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

    # Step 6: Determine overall availability and handle NO_AVAILABLE_SLOTS
    overall_available = any(s["available"] for s in slots) if slots else False

    if slots and not overall_available:
        avail_data = format_doctor_availability_out(
            doctor_id=str(doctor.doctor_id),
            check_date=check_date,
            available=False,
            slots=slots
        )
        return standard_response(
            success=False,
            data=avail_data,
            message="No available slots for the selected date",
            error_code="NO_AVAILABLE_SLOTS",
        )

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
    if "doctor_id" in data and "id" not in data:
        data["id"] = data.pop("doctor_id")
    if "id" in data and data["id"] is not None:
        data["id"] = _coerce_uuid(data["id"])
    if "is_available" in data and "status" not in data:
        data["status"] = "ACTIVE" if data.pop("is_available") else "INACTIVE"
    if "specialization" not in data:
        data["specialization"] = data.get("department", "General")

    doctor = Doctor(**data)
    db.session.add(doctor)
    db.session.commit()
    return doctor


def create_doctor_schedule(schedule_data: Dict[str, Any]) -> DoctorSchedule:
    """Helper to create a doctor schedule entry using Flask-SQLAlchemy db.session."""
    data = dict(schedule_data)
    if "id" in data and data["id"] is not None:
        data["id"] = _coerce_uuid(data["id"])
    if "doctor_id" in data and data["doctor_id"] is not None:
        data["doctor_id"] = _coerce_uuid(data["doctor_id"])
    schedule = DoctorSchedule(**data)
    db.session.add(schedule)
    db.session.commit()
    return schedule


def create_doctor_leave(leave_data: Dict[str, Any]) -> DoctorLeave:
    """Helper to create a doctor leave entry using Flask-SQLAlchemy db.session."""
    data = dict(leave_data)
    if "id" in data and data["id"] is not None:
        data["id"] = _coerce_uuid(data["id"])
    if "doctor_id" in data and data["doctor_id"] is not None:
        data["doctor_id"] = _coerce_uuid(data["doctor_id"])
    leave = DoctorLeave(**data)
    db.session.add(leave)
    db.session.commit()
    return leave
