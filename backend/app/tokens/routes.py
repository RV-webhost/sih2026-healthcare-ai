from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.tokens import service
from app.tokens.models import Token, TokenStatus
from app.tokens.schemas import (
    TokenCreateRequest, StandardResponse, TokenData, 
    ErrorCode
)

router = APIRouter(prefix="/api/tokens", tags=["Tokens & Queue"])

@router.post("", response_model=StandardResponse[TokenData], status_code=status.HTTP_201_CREATED)
def generate_token(payload: TokenCreateRequest, db: Session = Depends(get_db)):
    token = service.create_token(db, payload.patient_id, payload.appointment_id)
    people_ahead, wait_time = service.calculate_queue_metrics(db, token)
    
    return StandardResponse(
        success=True,
        message="Token generated successfully.",
        data=TokenData(
            token_id=str(token.id),
            token_number=token.token_number,
            patient_id=token.patient_id,
            appointment_id=token.appointment_id,
            doctor_id=token.doctor_id,
            token_date=token.token_date,
            status=token.status.value,
            people_ahead=people_ahead,
            estimated_wait_minutes=wait_time,
            created_at=token.created_at
        )
    )

@router.get("/{token_id}", response_model=StandardResponse[TokenData])
def get_token_status(token_id: str, db: Session = Depends(get_db)):
    token = db.query(Token).filter(Token.id == str(token_id)).first()
    if not token:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": "Token not found.", "error_code": ErrorCode.TOKEN_NOT_FOUND}
        )
    
    people_ahead, wait_time = service.calculate_queue_metrics(db, token)
    return StandardResponse(
        success=True,
        message="Token status retrieved successfully.",
        data=TokenData(
            token_id=str(token.id),
            token_number=token.token_number,
            patient_id=token.patient_id,
            appointment_id=token.appointment_id,
            doctor_id=token.doctor_id,
            token_date=token.token_date,
            status=token.status.value,
            people_ahead=people_ahead,
            estimated_wait_minutes=wait_time,
            created_at=token.created_at
        )
    )

@router.patch("/{token_id}/call", response_model=StandardResponse[TokenData])
def call_patient(token_id: str, db: Session = Depends(get_db)):
    token = service.transition_token_status(db, token_id, TokenStatus.CALLED)
    people_ahead, wait_time = service.calculate_queue_metrics(db, token)
    return StandardResponse(
        success=True,
        message="Patient called successfully.",
        data=TokenData(
            token_id=str(token.id),
            token_number=token.token_number,
            patient_id=token.patient_id,
            appointment_id=token.appointment_id,
            doctor_id=token.doctor_id,
            token_date=token.token_date,
            status=token.status.value,
            people_ahead=people_ahead,
            estimated_wait_minutes=wait_time,
            created_at=token.created_at
        )
    )

@router.patch("/{token_id}/skip", response_model=StandardResponse[TokenData])
def skip_patient(token_id: str, db: Session = Depends(get_db)):
    token = service.transition_token_status(db, token_id, TokenStatus.SKIPPED)
    return StandardResponse(
        success=True,
        message="Patient skipped.",
        data=TokenData(
            token_id=str(token.id),
            token_number=token.token_number,
            patient_id=token.patient_id,
            appointment_id=token.appointment_id,
            doctor_id=token.doctor_id,
            token_date=token.token_date,
            status=token.status.value,
            people_ahead=0,
            estimated_wait_minutes=0,
            created_at=token.created_at
        )
    )

@router.patch("/{token_id}/complete", response_model=StandardResponse[TokenData])
def complete_consultation(token_id: str, db: Session = Depends(get_db)):
    token = service.transition_token_status(db, token_id, TokenStatus.COMPLETED)
    return StandardResponse(
        success=True,
        message="Consultation completed.",
        data=TokenData(
            token_id=str(token.id),
            token_number=token.token_number,
            patient_id=token.patient_id,
            appointment_id=token.appointment_id,
            doctor_id=token.doctor_id,
            token_date=token.token_date,
            status=token.status.value,
            people_ahead=0,
            estimated_wait_minutes=0,
            created_at=token.created_at
        )
    )