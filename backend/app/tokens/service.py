from datetime import date, datetime, timezone
from typing import Optional, Tuple, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException, status

from app.tokens.models import Token, TokenStatus
from app.tokens.schemas import ErrorCode

AVG_CONSULTATION_MINUTES = 10

ALLOWED_TRANSITIONS = {
    TokenStatus.WAITING: {TokenStatus.CALLED, TokenStatus.CANCELLED, TokenStatus.SKIPPED},
    TokenStatus.CALLED: {TokenStatus.IN_CONSULTATION, TokenStatus.COMPLETED, TokenStatus.SKIPPED, TokenStatus.CANCELLED},
    TokenStatus.IN_CONSULTATION: {TokenStatus.COMPLETED, TokenStatus.CANCELLED},
    TokenStatus.SKIPPED: {TokenStatus.WAITING, TokenStatus.CANCELLED},
    TokenStatus.COMPLETED: set(),
    TokenStatus.CANCELLED: set(),
}

def verify_appointment(appointment_id: str, patient_id: str) -> Dict[str, Any]:
    if not appointment_id or not patient_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "Invalid appointment or patient ID", "error_code": ErrorCode.INVALID_APPOINTMENT}
        )
    return {"valid": True, "doctor_id": "D204", "status": "CONFIRMED"}

def calculate_queue_metrics(db: Session, token: Token) -> Tuple[int, int]:
    if token.status != TokenStatus.WAITING:
        return 0, 0

    people_ahead = db.query(func.count(Token.id)).filter(
        Token.doctor_id == token.doctor_id,
        Token.token_date == token.token_date,
        Token.status == TokenStatus.WAITING,
        Token.token_number < token.token_number
    ).scalar() or 0

    estimated_wait = people_ahead * AVG_CONSULTATION_MINUTES
    return people_ahead, estimated_wait

def create_token(db: Session, patient_id: str, appointment_id: str) -> Token:
    existing_token = db.query(Token).filter(Token.appointment_id == appointment_id).first()
    if existing_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "Token already exists for this appointment.", "error_code": ErrorCode.TOKEN_ALREADY_EXISTS}
        )

    appointment_data = verify_appointment(appointment_id, patient_id)
    doctor_id = appointment_data.get("doctor_id", "D204")
    today = date.today()

    max_token_num = db.query(func.max(Token.token_number)).filter(
        Token.doctor_id == doctor_id,
        Token.token_date == today
    ).scalar() or 0
    next_token_num = max_token_num + 1

    new_token = Token(
        patient_id=patient_id,
        appointment_id=appointment_id,
        doctor_id=str(doctor_id),
        token_date=today,
        token_number=next_token_num,
        status=TokenStatus.WAITING
    )
    db.add(new_token)
    db.commit()
    db.refresh(new_token)
    return new_token

def transition_token_status(db: Session, token_id: str, target_status: TokenStatus) -> Token:
    token = db.query(Token).filter(Token.id == str(token_id)).first()
    if not token:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": "Token not found.", "error_code": ErrorCode.TOKEN_NOT_FOUND}
        )

    allowed = ALLOWED_TRANSITIONS.get(token.status, set())
    if target_status not in allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": f"Cannot transition token from {token.status.value} to {target_status.value}.",
                "error_code": ErrorCode.INVALID_STATUS_TRANSITION
            }
        )

    token.status = target_status
    now = datetime.now(timezone.utc)
    if target_status == TokenStatus.CALLED:
        token.called_at = now
    elif target_status == TokenStatus.SKIPPED:
        token.skipped_at = now
    elif target_status in (TokenStatus.COMPLETED, TokenStatus.CANCELLED):
        token.completed_at = now

    db.commit()
    db.refresh(token)
    return token