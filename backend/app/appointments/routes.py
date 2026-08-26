from flask import Blueprint, request, jsonify
from marshmallow import ValidationError

from app.appointments import service
from app.appointments.schemas import (
    create_appointment_schema,
    update_appointment_schema,
)

appointments_bp = Blueprint("appointments", __name__)


def standard_response(success: bool, data=None, message: str = "", error_code: str = None, status_code: int = 200):
    return jsonify({
        "success": success,
        "data": data,
        "message": message,
        "error_code": error_code
    }), status_code


@appointments_bp.post("")
@appointments_bp.post("/")
def create_appointment_route():
    """
    POST /api/appointments
    Creates a new appointment.
    """
    json_data = request.get_json(silent=True)
    if not json_data:
        return standard_response(
            success=False,
            message="Invalid or missing JSON payload in request body.",
            error_code="INVALID_PAYLOAD",
            status_code=400
        )

    try:
        validated_data = create_appointment_schema.load(json_data)
    except ValidationError as err:
        return standard_response(
            success=False,
            data=err.messages,
            message=f"Validation failed: {err.messages}",
            error_code="VALIDATION_ERROR",
            status_code=400
        )

    appointment, message, error_code = service.create_appointment(
        patient_id=validated_data["patient_id"],
        doctor_id=validated_data["doctor_id"],
        appointment_date=validated_data["appointment_date"],
        appointment_time=validated_data["appointment_time"],
        reason=validated_data.get("reason"),
        status=validated_data.get("status", "CONFIRMED")
    )

    if error_code:
        status_code = 409 if error_code == "SLOT_UNAVAILABLE" else 400
        return standard_response(
            success=False,
            message=message,
            error_code=error_code,
            status_code=status_code
        )

    return standard_response(
        success=True,
        data=appointment.to_dict(),
        message=message,
        status_code=201
    )


@appointments_bp.get("/<appointment_id>")
def get_appointment_route(appointment_id):
    """
    GET /api/appointments/<id>
    Retrieves appointment details by ID.
    """
    appointment, message, error_code = service.get_appointment_by_id(appointment_id)

    if error_code:
        status_code = 404 if error_code == "APPOINTMENT_NOT_FOUND" else 400
        return standard_response(
            success=False,
            message=message,
            error_code=error_code,
            status_code=status_code
        )

    return standard_response(
        success=True,
        data=appointment.to_dict(),
        message=message,
        status_code=200
    )


@appointments_bp.get("/patient/<patient_id>")
def list_patient_appointments_route(patient_id):
    """
    GET /api/appointments/patient/<patient_id>
    Lists all appointments for a patient.
    """
    appointments, message, error_code = service.list_patient_appointments(patient_id)

    if error_code:
        return standard_response(
            success=False,
            message=message,
            error_code=error_code,
            status_code=400
        )

    return standard_response(
        success=True,
        data=[appt.to_dict() for appt in appointments],
        message=message,
        status_code=200
    )


@appointments_bp.patch("/<appointment_id>/cancel")
def cancel_appointment_route(appointment_id):
    """
    PATCH /api/appointments/<id>/cancel
    Cancels an existing appointment.
    """
    appointment, message, error_code = service.cancel_appointment(appointment_id)

    if error_code:
        status_code = 404 if error_code == "APPOINTMENT_NOT_FOUND" else 400
        return standard_response(
            success=False,
            message=message,
            error_code=error_code,
            status_code=status_code
        )

    return standard_response(
        success=True,
        data=appointment.to_dict(),
        message=message,
        status_code=200
    )


@appointments_bp.patch("/<appointment_id>/reschedule")
def reschedule_appointment_route(appointment_id):
    """
    PATCH /api/appointments/<id>/reschedule
    Reschedules an existing appointment to a new date/time.
    """
    json_data = request.get_json(silent=True)
    if not json_data:
        return standard_response(
            success=False,
            message="Invalid or missing JSON payload in request body.",
            error_code="INVALID_PAYLOAD",
            status_code=400
        )

    try:
        validated_data = update_appointment_schema.load(json_data)
    except ValidationError as err:
        return standard_response(
            success=False,
            data=err.messages,
            message=f"Validation failed: {err.messages}",
            error_code="VALIDATION_ERROR",
            status_code=400
        )

    new_date = validated_data.get("appointment_date")
    new_time = validated_data.get("appointment_time")

    if not new_date or not new_time:
        return standard_response(
            success=False,
            message="Both appointment_date (or date) and appointment_time (or time) are required for rescheduling.",
            error_code="VALIDATION_ERROR",
            status_code=400
        )

    appointment, message, error_code = service.reschedule_appointment(
        appointment_id=appointment_id,
        new_date=new_date,
        new_time=new_time
    )

    if error_code:
        if error_code == "APPOINTMENT_NOT_FOUND":
            status_code = 404
        elif error_code == "SLOT_UNAVAILABLE":
            status_code = 409
        else:
            status_code = 400

        return standard_response(
            success=False,
            message=message,
            error_code=error_code,
            status_code=status_code
        )

    return standard_response(
        success=True,
        data=appointment.to_dict(),
        message=message,
        status_code=200
    )
