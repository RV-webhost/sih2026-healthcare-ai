from __future__ import annotations

import enum
import uuid
from datetime import date as date_

from sqlalchemy import (
    Column,
    Date,
    DateTime,
    Enum as SAEnum,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
)

from app.database import Base


class TokenStatus(str, enum.Enum):
    WAITING = "WAITING"
    CALLED = "CALLED"
    IN_CONSULTATION = "IN_CONSULTATION"
    COMPLETED = "COMPLETED"
    SKIPPED = "SKIPPED"
    CANCELLED = "CANCELLED"


ACTIVE_QUEUE_STATUSES: tuple[TokenStatus, ...] = (TokenStatus.WAITING,)
OPEN_STATUSES: tuple[TokenStatus, ...] = (
    TokenStatus.WAITING,
    TokenStatus.CALLED,
    TokenStatus.IN_CONSULTATION,
)
TERMINAL_STATUSES: tuple[TokenStatus, ...] = (
    TokenStatus.COMPLETED,
    TokenStatus.SKIPPED,
    TokenStatus.CANCELLED,
)


class Token(Base):
    __tablename__ = "tokens"

    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        nullable=False,
    )
    token_number = Column(Integer, nullable=False)
    patient_id = Column(String(64), nullable=False, index=True)
    appointment_id = Column(String(64), nullable=False, unique=True, index=True)
    doctor_id = Column(String(64), nullable=False, index=True)
    token_date = Column(Date, nullable=False, index=True, default=date_.today)
    status = Column(
        SAEnum(
            TokenStatus,
            name="token_status",
            native_enum=False,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
        default=TokenStatus.WAITING,
        server_default=TokenStatus.WAITING.value,
        index=True,
    )

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    called_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    skipped_at = Column(DateTime(timezone=True), nullable=True)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint(
            "doctor_id", "token_date", "token_number", name="uq_tokens_doctor_date_number"
        ),
        Index("ix_tokens_doctor_date_status", "doctor_id", "token_date", "status"),
        Index("ix_tokens_doctor_date_number", "doctor_id", "token_date", "token_number"),
    )