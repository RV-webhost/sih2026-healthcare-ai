from datetime import date, datetime, timezone
from typing import Optional, Tuple, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func

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

def verify_appointment(
    appointment_id: str,
    patient_id: str,
) -> Dict[str, Any]:
    """
    Validate that the appointment exists and belongs to the patient,
    then return the doctor associated with that appointment.
    """
    if not appointment_id or not patient_id:
        raise ValueError(
            "INVALID_APPOINTMENT: Invalid appointment or patient ID"
        )

    from app.models.m2_models import Appointment

    appointment = Appointment.query.filter(
        Appointment.id == appointment_id,
        Appointment.patient_id == patient_id,
    ).first()

    if not appointment:
        raise ValueError(
            "INVALID_APPOINTMENT: Appointment not found or does not belong to patient"
        )

    if appointment.status != "CONFIRMED":
        raise ValueError(
            f"INVALID_APPOINTMENT: Appointment status is {appointment.status}"
        )

    return {
        "valid": True,
        "doctor_id": str(appointment.doctor_id),
        "status": appointment.status,
    }

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
        raise ValueError("TOKEN_ALREADY_EXISTS: Token already exists for this appointment.")

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
        raise ValueError("TOKEN_NOT_FOUND: Token not found.")

    allowed = ALLOWED_TRANSITIONS.get(token.status, set())
    if target_status not in allowed:
        raise ValueError(f"INVALID_STATUS_TRANSITION: Cannot transition token from {token.status.value} to {target_status.value}.")

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