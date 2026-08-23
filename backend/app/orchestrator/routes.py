from flask import Blueprint, jsonify, request
from marshmallow import ValidationError

from app.orchestrator.service import process_request
from .schemas import AssistantRequestSchema

orchestrator_bp = Blueprint("orchestrator", __name__)
assistant_request_schema = AssistantRequestSchema()


@orchestrator_bp.post("/assistant")
def process_assistant_request():
    payload = request.get_json(silent=True) or {}
    try:
        validated_data = assistant_request_schema.load(payload)
    except ValidationError as err:
        return jsonify({"success": False, "errors": err.messages}), 400

    return jsonify(process_request(validated_data))
