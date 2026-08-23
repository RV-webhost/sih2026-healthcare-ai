from flask import Blueprint, jsonify, request

orchestrator_bp = Blueprint("orchestrator", __name__)


@orchestrator_bp.post("/assistant")
def assistant():
    request.get_json(silent=True)

    return jsonify(
        {
            "success": True,
            "intent": "placeholder",
            "data": {},
            "message": "Orchestrator placeholder response",
            "next_action": None,
        }
    )
