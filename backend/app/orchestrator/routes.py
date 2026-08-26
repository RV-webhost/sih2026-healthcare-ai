from flask import Blueprint, request, jsonify
from pydantic import ValidationError
from app.auth.decorators import get_current_user  # M5 Auth dependency
from app.orchestrator.schemas import AssistantRequestSchema, build_error_response
from app.orchestrator.service import OrchestratorService

orchestrator_bp = Blueprint('orchestrator', __name__)

@orchestrator_bp.route('/assistant', methods=['POST'])
@get_current_user
def assistant_endpoint(current_user):
    """
    External API entry point for the AI Assistant[cite: 1].
    """
    # 1. Validate incoming JSON using your Pydantic schema
    if not request.is_json:
        error_resp = build_error_response(
            intent="UNKNOWN",
            message="Request must be JSON.",
            error_code="INVALID_CONTENT_TYPE",
            next_action=None
        )
        return jsonify(error_resp), 400

    try:
        request_data = AssistantRequestSchema(**request.json)
    except ValidationError as e:
        return jsonify({
            "success": False,
            "intent": "UNKNOWN",
            "message": "Invalid request format.",
            "error_code": "VALIDATION_ERROR",
            "errors": e.errors()
        }), 400

    # 2. Pass the validated message and M5 user context to the orchestrator service[cite: 1]
    response_data = OrchestratorService.process_request(
        message=request_data.message, 
        user=current_user
    )
    
    # 3. Return the final JSON[cite: 1]
    return jsonify(response_data), 200