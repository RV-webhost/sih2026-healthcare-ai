from flask import Blueprint, jsonify, request

from app.orchestrator.service import process_request

orchestrator_bp = Blueprint("orchestrator", __name__)


@orchestrator_bp.post("/assistant")
def process_assistant_request():
    payload = request.get_json(silent=True) or {}
    return jsonify(process_request(payload))
