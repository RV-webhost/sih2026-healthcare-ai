from enum import Enum

class AIIntent(str, Enum):
    BOOK_APPOINTMENT = "BOOK_APPOINTMENT"
    CANCEL_APPOINTMENT = "CANCEL_APPOINTMENT"
    RESCHEDULE_APPOINTMENT = "RESCHEDULE_APPOINTMENT"
    CHECK_DOCTOR_AVAILABILITY = "CHECK_DOCTOR_AVAILABILITY"
    CHECK_BED_AVAILABILITY = "CHECK_BED_AVAILABILITY"
    CHECK_TOKEN = "CHECK_TOKEN"
    VIEW_APPOINTMENTS = "VIEW_APPOINTMENTS"
    GENERAL_HEALTH_QUERY = "GENERAL_HEALTH_QUERY"
    UNKNOWN = "UNKNOWN"

def validate_ai_request(data: dict) -> tuple[bool, str | None]:
    """
    Validates that the incoming request has the required JSON shape:
    { "message": "patient text" }
    """
    if not data or "message" not in data:
        return False, "Missing 'message' field in request body."
    
    message = data.get("message")
    if not isinstance(message, str) or not message.strip():
        return False, "'message' must be a non-empty string."
        
    return True, None

def build_error_response(message: str, error_code: str = "INTENT_NOT_UNDERSTOOD") -> dict:
    """
    Builds the standard error response format mandated by the team.
    """
    return {
        "success": False,
        "intent": AIIntent.UNKNOWN.value,
        "entities": {},
        "confidence": 0.0,
        "message": message,
        "error_code": error_code
    }
