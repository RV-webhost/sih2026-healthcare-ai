import requests
from .formatters import (
    format_bed_response,
    format_doctor_availability_response,
    format_booking_response,
    format_cancellation_response,
    format_unknown_response
)

AI_SERVICE_URL = "http://127.0.0.1:5000/api/ai/understand"

# Mock/Local service endpoints or direct database queries
def process_user_query(message: str) -> dict:
    # 1. Step 2: Call Member 1's AI endpoint
    ai_response = requests.post(AI_SERVICE_URL, json={"message": message}).json()
    
    intent = ai_response.get("intent", "UNKNOWN")
    entities = ai_response.get("entities", {})
    
    final_reply = ""
    action_data = {}

    # 2. Step 3: Route based on intent & process
    if intent == "CHECK_BED_AVAILABILITY":
        bed_type = entities.get("bed_type") or "ICU"
        # Example database query/service result
        action_data = {"available_count": 6, "bed_type": bed_type, "ward": "Block B, 3rd Floor"}
        final_reply = format_bed_response(action_data, bed_type)

    elif intent == "CHECK_DOCTOR_AVAILABILITY":
        doctor_name = entities.get("doctor_name") or "Sharma"
        action_data = {"doctor_name": doctor_name, "available_slots": ["10:00 AM", "11:30 AM", "04:00 PM"]}
        final_reply = format_doctor_availability_response(action_data, entities)

    elif intent == "BOOK_APPOINTMENT":
        action_data = {
            "status": "CONFIRMED",
            "doctor_name": entities.get("doctor_name") or "General Physician",
            "date": entities.get("date") or "2026-08-25",
            "time": entities.get("time") or "10:00 AM",
            "appointment_id": "APT-9482"
        }
        final_reply = format_booking_response(action_data)

    elif intent == "CANCEL_APPOINTMENT":
        action_data = {"success": True, "appointment_id": "APT-9482"}
        final_reply = format_cancellation_response(action_data)

    else:
        final_reply = format_unknown_response()

    # 3. Step 4: Output payload to send back to user
    return {
        "success": True,
        "reply": final_reply,
        "intent": intent,
        "entities": entities,
        "data": action_data
    }
