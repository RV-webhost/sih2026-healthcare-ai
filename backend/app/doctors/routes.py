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
    Fetch all active doctors
    Fetch all active doctors, optionally filtered by specialization query parameter.
    ---
    tags:
      - Doctors
    parameters:
      - name: specialization
        in: query
        type: string
        required: false
        description: Filter doctors by specialization
      - name: department
        in: query
        type: string
        required: false
        description: Filter doctors by department (alias for specialization)
    responses:
      200:
        description: Active doctors fetched successfully
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            data:
              type: array
              items:
                type: object
                properties:
                  doctor_id:
                    type: string
                    example: "doc-test-1"
                  name:
                    type: string
                    example: "Dr. Sarah Connor"
                  department:
                    type: string
                    example: "Pediatrics"
                  is_available:
                    type: boolean
                    example: true
            message:
              type: string
              example: "Active doctors fetched successfully"
            error_code:
              type: string
              nullable: true
              example: null
    """
    try:
        department = request.args.get("department") or request.args.get("specialization")
        doctors = DoctorService.get_doctors(department=department)
        doctors_data = [format_doctor_out(doc) for doc in doctors]

        return jsonify(standard_response(
            success=True,
            data=doctors_data,
            message="Active doctors fetched successfully"
        )), 200
    except Exception as e:
        return jsonify(standard_response(
            success=False,
            data=[],
            message=f"Failed to fetch active doctors: {str(e)}",
            error_code="INTERNAL_ERROR"
        )), 500


@doctors_bp.route("/<doctor_id>", methods=["GET"])
def get_doctor_by_id(doctor_id: str):
    """
    Fetch doctor details by ID
    Fetch details for a specific doctor by doctor_id.
    ---
    tags:
      - Doctors
    parameters:
      - name: doctor_id
        in: path
        type: string
        required: true
        description: Unique identifier of the doctor
    responses:
      200:
        description: Doctor details retrieved successfully
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            data:
              type: object
              properties:
                doctor_id:
                  type: string
                  example: "doc-test-1"
                name:
                  type: string
                  example: "Dr. Sarah Connor"
                department:
                  type: string
                  example: "Pediatrics"
                is_available:
                  type: boolean
                  example: true
            message:
              type: string
              example: "Doctor details retrieved successfully"
            error_code:
              type: string
              nullable: true
              example: null
      404:
        description: Doctor not found
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            data:
              type: object
              nullable: true
              example: null
            message:
              type: string
              example: "Doctor not found"
            error_code:
              type: string
              example: "DOCTOR_NOT_FOUND"
    """
    try:
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
    except Exception as e:
        return jsonify(standard_response(
            success=False,
            data=None,
            message=f"Failed to retrieve doctor details: {str(e)}",
            error_code="INTERNAL_ERROR"
        )), 500


@doctors_bp.route("/<doctor_id>/schedule", methods=["GET"])
def get_doctor_schedule(doctor_id: str):
    """
    Fetch regular weekly schedule for a doctor
    Fetch regular weekly schedule and working hours for a doctor.
    ---
    tags:
      - Doctors
    parameters:
      - name: doctor_id
        in: path
        type: string
        required: true
        description: Unique identifier of the doctor
    responses:
      200:
        description: Doctor schedule retrieved successfully
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            data:
              type: array
              items:
                type: object
                properties:
                  day_of_week:
                    type: string
                    example: "Monday"
                  start_time:
                    type: string
                    example: "09:00"
                  end_time:
                    type: string
                    example: "17:00"
                  slot_duration:
                    type: integer
                    example: 30
            message:
              type: string
              example: "Doctor schedule retrieved successfully"
            error_code:
              type: string
              nullable: true
              example: null
      404:
        description: Doctor not found
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            data:
              type: array
              example: []
            message:
              type: string
              example: "Doctor not found"
            error_code:
              type: string
              example: "DOCTOR_NOT_FOUND"
    """
    try:
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
    except Exception as e:
        return jsonify(standard_response(
            success=False,
            data=[],
            message=f"Failed to retrieve doctor schedule: {str(e)}",
            error_code="INTERNAL_ERROR"
        )), 500


@doctors_bp.route("/<doctor_id>/availability", methods=["GET"])
def get_doctor_availability(doctor_id: str):
    """
    Calculate doctor availability and time slots
    Calculate doctor availability and time slots for a specific date (YYYY-MM-DD).
    ---
    tags:
      - Doctors
    parameters:
      - name: doctor_id
        in: path
        type: string
        required: true
        description: Unique identifier of the doctor
      - name: date
        in: query
        type: string
        format: date
        required: true
        description: Date to check availability in YYYY-MM-DD format
        example: "2026-08-24"
    responses:
      200:
        description: Doctor availability calculated successfully
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            data:
              type: object
              properties:
                doctor_id:
                  type: string
                  example: "doc-test-1"
                date:
                  type: string
                  example: "2026-08-24"
                available:
                  type: boolean
                  example: true
                slots:
                  type: array
                  items:
                    type: object
                    properties:
                      time:
                        type: string
                        example: "09:00"
                      available:
                        type: boolean
                        example: true
            message:
              type: string
              example: "Doctor availability calculated successfully"
            error_code:
              type: string
              nullable: true
              example: null
      400:
        description: Missing or invalid date parameter
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            data:
              type: object
              nullable: true
              example: null
            message:
              type: string
              example: "Invalid date format. Expected YYYY-MM-DD"
            error_code:
              type: string
              enum:
                - INVALID_DATE
              example: "INVALID_DATE"
      404:
        description: Doctor not found
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            data:
              type: object
              nullable: true
              example: null
            message:
              type: string
              example: "Doctor not found"
            error_code:
              type: string
              example: "DOCTOR_NOT_FOUND"
    """
    date_str = request.args.get("date")
    if not date_str:
        return jsonify(standard_response(
            success=False,
            data=None,
            message="Query parameter 'date' (YYYY-MM-DD) is required",
            error_code="INVALID_DATE"
        )), 400

    try:
        check_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return jsonify(standard_response(
            success=False,
            data=None,
            message="Invalid date format. Expected YYYY-MM-DD",
            error_code="INVALID_DATE"
        )), 400

    try:
        result = DoctorService.calculate_availability(
            doctor_id=doctor_id,
            check_date=check_date
        )

        error_code = result.get("error_code")

        if error_code == "DOCTOR_NOT_FOUND":
            return jsonify(result), 404

        return jsonify(result), 200
    except Exception as e:
        return jsonify(standard_response(
            success=False,
            data=None,
            message=f"Failed to calculate doctor availability: {str(e)}",
            error_code="INTERNAL_ERROR"
        )), 500

