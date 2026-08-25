from contextlib import contextmanager

from flask import Blueprint, jsonify, request

from app.database import SessionLocal
from app.tokens import service
from app.tokens.models import Token, TokenStatus
from app.tokens.schemas import ErrorCode

tokens_bp = Blueprint("tokens", __name__, url_prefix="/api/v1/tokens")


@contextmanager
def _db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _serialize_token(token: Token, people_ahead: int, wait_time: int) -> dict:
    return {
        "token_id": str(token.id),
        "token_number": token.token_number,
        "patient_id": token.patient_id,
        "appointment_id": token.appointment_id,
        "doctor_id": token.doctor_id,
        "token_date": token.token_date.isoformat() if token.token_date else None,
        "status": token.status.value,
        "people_ahead": people_ahead,
        "estimated_wait_minutes": wait_time,
        "created_at": token.created_at.isoformat() if token.created_at else None,
    }


def _success(message: str, data: dict, status_code: int = 200):
    return jsonify({"success": True, "message": message, "data": data}), status_code


def _error_response(exc: Exception):
    status_code = getattr(exc, "status_code", 500)
    detail = getattr(exc, "detail", None)
    if isinstance(detail, dict):
        error_code = detail.get("error_code")
        if hasattr(error_code, "value"):
            error_code = error_code.value
        return jsonify({
            "success": False,
            "data": None,
            "message": detail.get("message", str(exc)),
            "error_code": error_code,
        }), status_code
    return jsonify({
        "success": False,
        "data": None,
        "message": str(exc),
        "error_code": ErrorCode.INTERNAL_ERROR.value,
    }), 500 if not isinstance(status_code, int) else status_code


@tokens_bp.route("", methods=["POST"], strict_slashes=False)
def generate_token():
    payload = request.get_json(silent=True) or {}
    patient_id = payload.get("patient_id")
    appointment_id = payload.get("appointment_id")

    if not patient_id or not appointment_id:
        return jsonify({
            "success": False,
            "data": None,
            "message": "patient_id and appointment_id are required.",
            "error_code": ErrorCode.VALIDATION_ERROR.value,
        }), 400

    with _db_session() as db:
        try:
            token = service.create_token(db, patient_id, appointment_id)
            people_ahead, wait_time = service.calculate_queue_metrics(db, token)
            return _success(
                "Token generated successfully.",
                _serialize_token(token, people_ahead, wait_time),
                201,
            )
        except Exception as exc:
            return _error_response(exc)




@tokens_bp.route('/queue', methods=['GET'])
def get_queue():
    doctor_id = request.args.get('doctor_id')
    date_str = request.args.get('date')
    
    if not doctor_id or not date_str:
        return jsonify({"success": False, "message": "Missing doctor_id or date"}), 400
        
    # TODO: Connect to actual service logic for queue retrieval
    return jsonify({
        "success": True,
        "data": {
            "doctor_id": doctor_id,
            "date": date_str,
            "current_token": 0,
            "queue": []
        },
        "message": "Queue retrieved successfully."
    }), 200

@tokens_bp.route('/current', methods=['GET'])
def get_current_token():
    doctor_id = request.args.get('doctor_id')
    date_str = request.args.get('date')
    
    if not doctor_id or not date_str:
        return jsonify({"success": False, "message": "Missing doctor_id or date"}), 400
        
    # TODO: Connect to actual service logic for current token
    return jsonify({
        "success": True,
        "data": {
            "doctor_id": doctor_id,
            "current_token": 0,
            "next_token": 1
        }
    }), 200


@tokens_bp.route("/<token_id>", methods=["GET"], strict_slashes=False)
def get_token_status(token_id: str):
    with _db_session() as db:
        token = db.query(Token).filter(Token.id == str(token_id)).first()
        if not token:
            return jsonify({
                "success": False,
                "data": None,
                "message": "Token not found.",
                "error_code": ErrorCode.TOKEN_NOT_FOUND.value,
            }), 404

        people_ahead, wait_time = service.calculate_queue_metrics(db, token)
        return _success(
            "Token status retrieved successfully.",
            _serialize_token(token, people_ahead, wait_time),
        )


@tokens_bp.route("/<token_id>/call", methods=["PATCH"], strict_slashes=False)
def call_patient(token_id: str):
    with _db_session() as db:
        try:
            token = service.transition_token_status(db, token_id, TokenStatus.CALLED)
            people_ahead, wait_time = service.calculate_queue_metrics(db, token)
            return _success(
                "Patient called successfully.",
                _serialize_token(token, people_ahead, wait_time),
            )
        except Exception as exc:
            return _error_response(exc)


@tokens_bp.route("/<token_id>/skip", methods=["PATCH"], strict_slashes=False)
def skip_patient(token_id: str):
    with _db_session() as db:
        try:
            token = service.transition_token_status(db, token_id, TokenStatus.SKIPPED)
            return _success(
                "Patient skipped.",
                _serialize_token(token, 0, 0),
            )
        except Exception as exc:
            return _error_response(exc)


@tokens_bp.route("/<token_id>/complete", methods=["PATCH"], strict_slashes=False)
def complete_consultation(token_id: str):
    with _db_session() as db:
        try:
            token = service.transition_token_status(db, token_id, TokenStatus.COMPLETED)
            return _success(
                "Consultation completed.",
                _serialize_token(token, 0, 0),
            )
        except Exception as exc:
            return _error_response(exc)

