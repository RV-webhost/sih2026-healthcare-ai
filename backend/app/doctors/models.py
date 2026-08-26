import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.hybrid import hybrid_property
from app.extensions import db


class Doctor(db.Model):
    __tablename__ = "doctors"

    id = db.Column(db.String(50), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(255), nullable=False)
    specialization = db.Column(db.String(255), nullable=False, index=True)
    department = db.Column(db.String(255), nullable=False)
    qualification = db.Column(db.String(255), nullable=True)
    experience = db.Column(db.Integer, nullable=True)
    status = db.Column(db.String(50), default="ACTIVE", nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    schedules = db.relationship("DoctorSchedule", backref="doctor", lazy=True, cascade="all, delete-orphan")
    leaves = db.relationship("DoctorLeave", backref="doctor", lazy=True, cascade="all, delete-orphan")

    @hybrid_property
    def doctor_id(self) -> str:
        return str(self.id) if self.id is not None else ""

    @doctor_id.setter
    def doctor_id(self, value) -> None:
        self.id = str(value) if value is not None else None

    @doctor_id.expression
    def doctor_id(cls):
        return cls.id

    @property
    def is_available(self) -> bool:
        return self.status == "ACTIVE"

    @is_available.setter
    def is_available(self, value: bool) -> None:
        self.status = "ACTIVE" if value else "INACTIVE"

    def __repr__(self) -> str:
        return f"<Doctor {self.name} ({self.specialization})>"


class DoctorSchedule(db.Model):
    __tablename__ = "doctor_schedules"

    id = db.Column(db.String(50), primary_key=True, default=lambda: str(uuid.uuid4()))
    doctor_id = db.Column(db.String(50), db.ForeignKey("doctors.id", ondelete="CASCADE"), nullable=False)
    day_of_week = db.Column(db.String(50), nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    slot_duration = db.Column(db.Integer, default=30, nullable=False)

    def __repr__(self) -> str:
        return f"<DoctorSchedule {self.day_of_week} {self.start_time}-{self.end_time}>"


class DoctorLeave(db.Model):
    __tablename__ = "doctor_leaves"

    id = db.Column(db.String(50), primary_key=True, default=lambda: str(uuid.uuid4()))
    doctor_id = db.Column(db.String(50), db.ForeignKey("doctors.id", ondelete="CASCADE"), nullable=False)
    leave_date = db.Column(db.Date, nullable=False, index=True)
    reason = db.Column(db.String(255), nullable=True)

    def __repr__(self) -> str:
        return f"<DoctorLeave {self.doctor_id} on {self.leave_date}>"
