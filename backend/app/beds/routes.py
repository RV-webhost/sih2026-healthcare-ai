from flask import Blueprint, request, jsonify
from marshmallow import ValidationError

from app.beds import service
from app.beds.schemas import allocate_bed_schema

beds_bp = Blueprint("beds", __name__)


def standard_response(success: bool, data=None, message: str = "", error_code: str = None, status_code: int = 200):
    return jsonify({
        "success": success,
        "data": data,
        "message": message,
        "error_code": error_code
    }), status_code


@beds_bp.get("/availability")
def get_bed_availability_route():
    """
    GET /api/beds/availability?ward=ICU
    Calculates overall bed availability or filtered by ward.
    """
    ward_filter = request.args.get("ward") or request.args.get("ward_type")
    data, message, error_code = service.get_bed_availability(ward_type=ward_filter)

    if error_code:
        return standard_response(
            success=False,
            message=message,
            error_code=error_code,
            status_code=500
        )

    return standard_response(
        success=True,
        data=data,
        message=message,
        status_code=200
    )


@beds_bp.post("/allocate")
def allocate_bed_route():
    """
    POST /api/beds/allocate
    Allocates an available bed in the requested ward.
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
        validated_data = allocate_bed_schema.load(json_data)
    except ValidationError as err:
        return standard_response(
            success=False,
            data=err.messages,
            message=f"Validation failed: {err.messages}",
            error_code="VALIDATION_ERROR",
            status_code=400
        )

    result, message, error_code = service.allocate_bed(
        patient_id=validated_data["patient_id"],
        ward_type=validated_data["ward_type"],
        bed_type=validated_data.get("bed_type")
    )

    if error_code:
        status_code = 409 if error_code == "BED_UNAVAILABLE" else 400
        return standard_response(
            success=False,
            message=message,
            error_code=error_code,
            status_code=status_code
        )

    return standard_response(
        success=True,
        data=result,
        message=message,
        status_code=201
    )


@beds_bp.patch("/<bed_id>/release")
def release_bed_route(bed_id):
    """
    PATCH /api/beds/<id>/release
    Releases an occupied bed and closes the active allocation.
    """
    result, message, error_code = service.release_bed(bed_id)

    if error_code:
        if error_code == "BED_NOT_FOUND":
            status_code = 404
        elif error_code == "BED_NOT_OCCUPIED":
            status_code = 400
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
        data=result,
        message=message,
        status_code=200
    )


@beds_bp.get("/<bed_id>")
def get_bed_route(bed_id):
    """
    GET /api/beds/<id>
    Retrieves bed information by ID.
    """
    bed_data, message, error_code = service.get_bed_by_id(bed_id)

    if error_code:
        status_code = 404 if error_code == "BED_NOT_FOUND" else 400
        return standard_response(
            success=False,
            message=message,
            error_code=error_code,
            status_code=status_code
        )

    return standard_response(
        success=True,
        data=bed_data,
        message=message,
        status_code=200
    )
