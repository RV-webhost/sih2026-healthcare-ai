from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

# ---------------------------------------------------------
# INCOMING REQUEST SCHEMA
# ---------------------------------------------------------
class AssistantRequestSchema(BaseModel):
    """What the frontend sends to the Orchestrator (M6)"""
    message: str = Field(..., description="The natural language message from the patient")
    
# ---------------------------------------------------------
# OUTGOING RESPONSE SCHEMA
# ---------------------------------------------------------
class AssistantResponseSchema(BaseModel):
    """The strict JSON contract M6 returns to the frontend"""
    success: bool
    intent: str
    data: Optional[Dict[str, Any]] = None
    message: str
    next_action: Optional[str] = None
    error_code: Optional[str] = None

# Helper function to easily format successful responses
def build_success_response(intent: str, message: str, data: dict = None, next_action: str = None) -> dict:
    return AssistantResponseSchema(
        success=True,
        intent=intent,
        data=data or {},
        message=message,
        next_action=next_action
    ).model_dump(exclude_none=True)

# Helper function to easily format error responses
def build_error_response(intent: str, message: str, error_code: str, next_action: str = "CLARIFY") -> dict:
    return AssistantResponseSchema(
        success=False,
        intent=intent,
        data=None,
        message=message,
        next_action=next_action,
        error_code=error_code
    ).model_dump(exclude_none=True)