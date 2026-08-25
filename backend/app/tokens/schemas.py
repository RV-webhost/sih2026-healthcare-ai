from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Any, Generic, List, Optional, TypeVar
from pydantic import BaseModel, ConfigDict, Field

from app.tokens.models import TokenStatus

__all__ = [
    "TokenStatus",
    "ErrorCode",
    "TokenCreateRequest",
    "QueueQueryParams",
    "CurrentTokenQueryParams",
    "TokenCreateData",
    "TokenStatusData",
    "TokenData",
    "QueueTokenItem",
    "QueueData",
    "CurrentTokenData",
    "TokenActionData",
    "SuccessResponse",
    "ErrorResponse",
    "StandardResponse",
    "TokenResponse",
    "TokenCreateResponse",
    "TokenStatusResponse",
    "QueueResponse",
    "CurrentTokenResponse",
    "TokenActionResponse",
]


class ErrorCode(str, Enum):
    APPOINTMENT_NOT_FOUND = "APPOINTMENT_NOT_FOUND"
    INVALID_APPOINTMENT = "INVALID_APPOINTMENT"
    TOKEN_ALREADY_EXISTS = "TOKEN_ALREADY_EXISTS"
    QUEUE_NOT_FOUND = "QUEUE_NOT_FOUND"
    TOKEN_NOT_FOUND = "TOKEN_NOT_FOUND"
    INVALID_STATUS_TRANSITION = "INVALID_STATUS_TRANSITION"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class TokenCreateRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    patient_id: str = Field(..., min_length=1, max_length=64)
    appointment_id: str = Field(..., min_length=1, max_length=64)


class QueueQueryParams(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    doctor_id: str = Field(..., min_length=1, max_length=64)
    date: Optional[date] = None


class CurrentTokenQueryParams(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    doctor_id: str = Field(..., min_length=1, max_length=64)
    date: Optional[date] = None


class TokenCreateData(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    token_id: str
    token_number: int
    patient_id: str
    appointment_id: Optional[str] = None
    doctor_id: str
    token_date: Optional[date] = None
    status: str
    people_ahead: int = Field(default=0, ge=0)
    estimated_wait_minutes: int = Field(default=0, ge=0)
    created_at: Optional[datetime] = None


class TokenStatusData(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    token_id: str
    token_number: int
    doctor_id: str
    token_date: Optional[date] = None
    status: str
    people_ahead: int = Field(default=0, ge=0)
    estimated_wait_minutes: int = Field(default=0, ge=0)


class QueueTokenItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    token_id: str
    token_number: int
    patient_id: str
    status: str
    created_at: datetime


class QueueData(BaseModel):
    doctor_id: str
    date: date
    current_token: Optional[int] = None
    queue: list[QueueTokenItem] = Field(default_factory=list)


class CurrentTokenData(BaseModel):
    doctor_id: str
    date: date
    current_token: Optional[int] = None
    current_token_id: Optional[str] = None
    current_status: Optional[str] = None
    next_token: Optional[int] = None
    next_token_id: Optional[str] = None


class TokenActionData(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    token_id: str
    token_number: int
    doctor_id: str
    patient_id: str
    status: str
    called_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    skipped_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None


T = TypeVar("T")


class SuccessResponse(BaseModel, Generic[T]):
    success: bool = True
    data: T
    message: str


class ErrorResponse(BaseModel):
    success: bool = False
    data: None = None
    message: str
    error_code: ErrorCode


class StandardResponse(BaseModel, Generic[T]):
    success: bool = True
    message: str = "Success"
    data: Optional[T] = None


TokenData = TokenCreateData
TokenResponse = StandardResponse[TokenData]
TokenCreateResponse = SuccessResponse[TokenCreateData]
TokenStatusResponse = SuccessResponse[TokenStatusData]
QueueResponse = SuccessResponse[QueueData]
CurrentTokenResponse = SuccessResponse[CurrentTokenData]
TokenActionResponse = SuccessResponse[TokenActionData]