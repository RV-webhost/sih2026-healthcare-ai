from typing import Any, Optional, Dict, List
from datetime import date, time, datetime


def standard_response(
    success: bool = True,
    data: Optional[Any] = None,
    message: str = "",
    error_code: Optional[str] = None
) -> Dict[str, Any]:
    """Generates the standard response dictionary matching the team API contract."""
    return {
        "success": success,
        "data": data,
        "message": message,
        "error_code": error_code,
    }


def format_doctor_out(doctor: Any) -> Dict[str, Any]:
    """Formats a Doctor model instance into DoctorOut dictionary structure."""
    if not doctor:
        return {}
    return {
        "doctor_id": str(getattr(doctor, "doctor_id", getattr(doctor, "id", ""))),
        "name": getattr(doctor, "name", ""),
        "department": getattr(doctor, "department", ""),
        "is_available": getattr(doctor, "is_available", True),
    }


def format_doctor_schedule_out(schedule: Any) -> Dict[str, Any]:
    """Formats a DoctorSchedule model instance into DoctorScheduleOut dictionary structure."""
    if not schedule:
        return {}
    start_t = getattr(schedule, "start_time", None)
    end_t = getattr(schedule, "end_time", None)

    start_str = start_t.strftime("%H:%M") if isinstance(start_t, time) else str(start_t) if start_t else ""
    end_str = end_t.strftime("%H:%M") if isinstance(end_t, time) else str(end_t) if end_t else ""

    return {
        "day_of_week": getattr(schedule, "day_of_week", ""),
        "start_time": start_str,
        "end_time": end_str,
        "slot_duration": getattr(schedule, "slot_duration", 30),
    }


def format_slot_out(time_str: str, available: bool) -> Dict[str, Any]:
    """Formats an individual time slot into SlotOut dictionary structure."""
    return {
        "time": time_str,
        "available": available,
    }


def format_doctor_availability_out(
    doctor_id: str,
    check_date: Any,
    available: bool,
    slots: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Formats availability calculation result into DoctorAvailabilityOut dictionary structure."""
    date_str = check_date.isoformat() if isinstance(check_date, (date, datetime)) else str(check_date)
    return {
        "doctor_id": str(doctor_id),
        "date": date_str,
        "available": available,
        "slots": slots,
    }
