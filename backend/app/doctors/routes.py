from datetime import datetime
from flask import Blueprint, request, jsonify

from app.doctors.schemas import (
    standard_response,
    format_doctor_out,
)
import app.doctors.service as DoctorService

doctors_bp = Blueprint("doctors", __name__, url_prefix="/api/v1/doctors")


@doctors_bp.route("", methods=["GET"])
@doctors_bp.route("/", methods=["GET"])
def get_doctors():
    """
    Fetch all active doctors, optionally filtered by specialization query parameter.
    """
    department = request.args.get("department") or request.args.get("specialization")
    doctors = DoctorService.get_doctors(department=department)
    doctors_data = [format_doctor_out(doc) for doc in doctors]

    return jsonify(standard_response(
        success=True,
        data=doctors_data,
        message="Active doctors fetched successfully"
    )), 200


@doctors_bp.route("/<doctor_id>", methods=["GET"])
def get_doctor_by_id(doctor_id: str):
    """
    Fetch details for a specific doctor by doctor_id.
    """
    doctor = DoctorService.get_doctor_by_id(doctor_id)
    if not doctor:
        return jsonify(standard_response(
            success=False,
            data=None,
            message="Doctor not found",
            error_code="DOCTOR_NOT_FOUND"
        )), 404

    return jsonify(standard_response(
        success=True,
        data=format_doctor_out(doctor),
        message="Doctor details retrieved successfully"
    )), 200


@doctors_bp.route("/<doctor_id>/schedule", methods=["GET"])
def get_doctor_schedule(doctor_id: str):
    """
    Fetch regular weekly schedule for a doctor.
    """
    doctor = DoctorService.get_doctor_by_id(doctor_id)
    if not doctor:
        return jsonify(standard_response(
            success=False,
            data=[],
            message="Doctor not found",
            error_code="DOCTOR_NOT_FOUND"
        )), 404

    schedules = DoctorService.get_doctor_schedule(doctor_id)
    return jsonify(standard_response(
        success=True,
        data=schedules,
        message="Doctor schedule retrieved successfully"
    )), 200


@doctors_bp.route("/<doctor_id>/availability", methods=["GET"])
def get_doctor_availability(doctor_id: str):
    """
    Calculate doctor availability and time slots for a specific date (YYYY-MM-DD).
    """
    date_str = request.args.get("date")
    if not date_str:
        return jsonify(standard_response(
            success=False,
            data=None,
            message="Query parameter 'date' (YYYY-MM-DD) is required",
            error_code="INVALID_INPUT"
        )), 400

    try:
        check_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return jsonify(standard_response(
            success=False,
            data=None,
            message="Invalid date format. Expected YYYY-MM-DD",
            error_code="INVALID_DATE_FORMAT"
        )), 400

    result = DoctorService.calculate_availability(
        doctor_id=doctor_id,
        check_date=check_date,
        booked_slots=[]
    )

    error_code = result.get("error_code")

    if not result.get("success"):
        if error_code == "DOCTOR_NOT_FOUND":
            return jsonify(result), 404
        elif error_code in ["DOCTOR_INACTIVE", "DOCTOR_ON_LEAVE"]:
            return jsonify(result), 400
        else:
            return jsonify(result), 400

    if error_code in ["DOCTOR_INACTIVE", "DOCTOR_ON_LEAVE"]:
        return jsonify(result), 400

    return jsonify(result), 200
