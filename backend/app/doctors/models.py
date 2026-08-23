import uuid
from app.extensions import db


class Doctor(db.Model):
    __tablename__ = "doctors"

    doctor_id = db.Column(db.String(255), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(255), nullable=False)
    department = db.Column(db.String(255), nullable=True)
    is_available = db.Column(db.Boolean, default=True)

    schedules = db.relationship("DoctorSchedule", backref="doctor", lazy=True, cascade="all, delete-orphan")
    leaves = db.relationship("DoctorLeave", backref="doctor", lazy=True, cascade="all, delete-orphan")

    @property
    def id(self) -> str:
        return str(self.doctor_id)


class DoctorSchedule(db.Model):
    __tablename__ = "doctor_schedules"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    doctor_id = db.Column(db.String(255), db.ForeignKey("doctors.doctor_id", ondelete="CASCADE"), nullable=False)
    day_of_week = db.Column(db.String(50), nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    slot_duration = db.Column(db.Integer, default=30, nullable=False)


class DoctorLeave(db.Model):
    __tablename__ = "doctor_leaves"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    doctor_id = db.Column(db.String(255), db.ForeignKey("doctors.doctor_id", ondelete="CASCADE"), nullable=False)
    leave_date = db.Column(db.Date, nullable=False, index=True)
    reason = db.Column(db.String(255), nullable=True)

