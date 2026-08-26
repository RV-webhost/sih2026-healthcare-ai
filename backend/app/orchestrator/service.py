from app.ai.service import extract_intent_and_entities # M1: AI Module
from app.orchestrator.schemas import build_success_response, build_error_response

# Downstream service imports (M2, M3, M4, M5)
from app.doctors.service import check_doctor_availability # M3
from app.beds.service import check_bed_availability       # M2
from app.tokens.service import get_queue_status           # M4
from app.auth.service import get_patient_profile          # M5

# Handlers for complex multi-step workflows
from app.orchestrator.handlers.appointment import AppointmentHandler

class OrchestratorService:
    @staticmethod
    def process_request(message: str, user: dict) -> dict:
        """
        Receives user message, queries M1 for intent, and routes to correct service.
        """
        try:
            # 1. M1 Understands the request[cite: 1]
            m1_response = extract_intent_and_entities(message)
            intent = m1_response.get('intent', 'UNKNOWN')
            entities = m1_response.get('entities', {})

            # 2. Decide the Workflow based on Intent[cite: 1]
            
            # --- APPOINTMENT WORKFLOWS ---
            if intent == 'BOOK_APPOINTMENT':
                return AppointmentHandler.handle_booking(entities, user)
                
            elif intent == 'CANCEL_APPOINTMENT':
                return AppointmentHandler.handle_cancellation(entities, user)

            # --- DOCTOR WORKFLOWS ---
            elif intent in ['CHECK_DOCTOR_AVAILABILITY', 'FIND_DOCTOR']:
                result = check_doctor_availability(entities)
                return build_success_response(
                    intent=intent,
                    message="Here is the doctor availability.",
                    data=result
                )

            # --- BED WORKFLOWS ---
            elif intent in ['CHECK_BED_AVAILABILITY', 'REQUEST_BED']:
                result = check_bed_availability(entities)
                return build_success_response(
                    intent=intent,
                    message="Here is the current bed availability.",
                    data=result
                )

            # --- TOKEN/QUEUE WORKFLOWS ---
            elif intent in ['CHECK_TOKEN', 'JOIN_QUEUE']:
                result = get_queue_status(user.get('patient_id'))
                return build_success_response(
                    intent=intent,
                    message="Here is your queue status.",
                    data=result
                )

            # --- PATIENT/AUTH WORKFLOWS ---
            elif intent == 'PATIENT_PROFILE':
                result = get_patient_profile(user.get('patient_id'))
                return build_success_response(
                    intent=intent,
                    message="Here is your profile information.",
                    data=result
                )

            # --- MISSING / UNKNOWN INTENTS[cite: 1] ---
            else:
                return build_error_response(
                    intent="UNKNOWN",
                    message="I couldn't understand your request. Please tell me what healthcare service you need.",
                    error_code="UNRECOGNIZED_INTENT",
                    next_action="CLARIFY"
                )

        except Exception as e:
            # Catch any unexpected backend errors to maintain the strict JSON contract
            return build_error_response(
                intent="SYSTEM_ERROR",
                message="An unexpected error occurred while processing your request.",
                error_code="INTERNAL_SERVER_ERROR",
                next_action="RETRY"
            )