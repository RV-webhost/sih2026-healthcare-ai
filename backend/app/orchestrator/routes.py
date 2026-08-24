from flask import Blueprint, request, jsonify
from .service import process_user_query

orchestrator_bp = Blueprint("orchestrator", __name__, url_prefix="/api/chat")

@orchestrator_bp.route("", methods=["POST"])
def chat():
    payload = request.get_json() or {}
    message = payload.get("message", "").strip()
    
    if not message:
        return jsonify({"success": False, "error": "Message is required"}), 400
        
    result = process_user_query(message)
    return jsonify(result), 200
