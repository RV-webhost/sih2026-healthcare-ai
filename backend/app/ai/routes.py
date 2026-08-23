from flask import Blueprint, request, jsonify
from app.extensions import db
from app.ai.models import AIRequest
from app.ai.schemas import validate_ai_request, build_error_response
from app.ai.service import process_ai_request

ai_bp = Blueprint('ai', __name__)

@ai_bp.route('/understand', methods=['POST'])
def understand_intent():
    """
    Endpoint: POST /api/v1/ai/understand (or /api/ai/understand)
    Receives user message, extracts intent/entities, logs the request, and returns JSON.
    """
    data = request.get_json() or {}
    
    # 1. Validate incoming JSON
    is_valid, error_msg = validate_ai_request(data)
    if not is_valid:
        return jsonify(build_error_response(error_msg, "VALIDATION_ERROR")), 400
        
    user_message = data.get('message', '').strip()
    
    # 2. Process via AI service
    result = process_ai_request(user_message)
    
    # 3. Log into ai_requests table
    try:
        log_entry = AIRequest(
            message=user_message,
            intent=result.get("intent", "UNKNOWN"),
            entities=result.get("entities", {}),
            confidence=result.get("confidence", 0.0)
        )
        db.session.add(log_entry)
        db.session.commit()
    except Exception as db_err:
        db.session.rollback()
        # Logging error should not crash the response to the user/orchestrator
        print(f"[Warning] Failed to log AI request to DB: {db_err}")
        
    # 4. Return standard JSON response
    status_code = 200 if result.get("success", False) else 400
    return jsonify(result), status_code
