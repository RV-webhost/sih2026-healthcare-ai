import json
import os
from flask import Blueprint, request, jsonify
from google import genai

from app.ai.prompts import get_system_prompt

ai_bp = Blueprint("ai", __name__)
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

def process_ai_request(message: str) -> dict:
    """Helper function to execute LLM request, allowing test mocks to hook in."""
    prompt = get_system_prompt() + f'\n\nPatient Message: "{message}"'
    
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )
    raw_text = response.text.strip().replace("```json", "").replace("```", "")
    return json.loads(raw_text)

# ---------------------------------------------------------
# ENDPOINT 1: Text to JSON (Multilingual to English JSON)
# ---------------------------------------------------------
@ai_bp.route("/understand", methods=["POST"])
def understand_intent():
    payload = request.get_json() or {}
    message = payload.get("message", "")
    
    # Validation check for missing/empty input (Fixes 500 -> 400 error)
    if not message or not str(message).strip():
        return jsonify({
            "success": False,
            "intent": "UNKNOWN",
            "entities": {},
            "confidence": 0.0,
            "message": "Message parameter is required and cannot be empty.",
            "error_code": "VALIDATION_ERROR"
        }), 400
    
    try:
        result = process_ai_request(message)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ---------------------------------------------------------
# ENDPOINT 2: JSON to NLP (English JSON to Multilingual Reply)
# ---------------------------------------------------------
@ai_bp.route("/generate-reply", methods=["POST"])
def generate_reply():
    payload = request.get_json() or {}
    intent = payload.get("intent")
    patient_message = payload.get("message")
    backend_data = payload.get("backend_data")
    
    prompt = f"""
    You are an empathetic hospital AI assistant.
    Patient's Original Message: "{patient_message}"
    System Intent: {intent}
    Backend Data: {json.dumps(backend_data)}
    
    RULES:
    1. Convert the Backend Data into a natural, friendly 1-2 sentence reply.
    2. CRITICAL: Reply in the EXACT SAME LANGUAGE the patient used in their Original Message.
    3. Do not include raw JSON in your reply.
    """
    
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        return jsonify({"success": True, "generated_reply": response.text.strip()}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500