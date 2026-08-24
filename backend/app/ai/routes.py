import json
import os
from flask import Blueprint, request, jsonify
from google import genai

# Initialize Blueprint and Gemini Client
ai_bp = Blueprint("ai", __name__)
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# ---------------------------------------------------------
# ENDPOINT 1: Text to JSON (Multilingual to English JSON)
# ---------------------------------------------------------
@ai_bp.route("/understand", methods=["POST"])
def understand_intent():
    payload = request.get_json() or {}
    message = payload.get("message", "")
    
    prompt = f"""
    You are a healthcare intent extraction AI. The user may speak in Marathi, Hindi, or English.
    
    RULES:
    1. Identify intent (CHECK_BED_AVAILABILITY, BOOK_APPOINTMENT, CHECK_DOCTOR_AVAILABILITY, CANCEL_APPOINTMENT, UNKNOWN).
    2. Extract entities (doctor_name, bed_type, date, time).
    3. CRITICAL: Translate all entities to English (e.g., 'हृदयरोगतज्ज्ञ' becomes 'CARDIOLOGY').
    
    Output ONLY valid JSON with keys: 'intent', 'entities', 'success' (boolean).
    
    User Message: "{message}"
    """
    
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        # Clean the response to ensure it parses as JSON
        raw_text = response.text.strip().replace("```json", "").replace("```", "")
        return jsonify(json.loads(raw_text)), 200
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
