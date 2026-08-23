import uuid
from datetime import datetime, timezone
from app.extensions import db

# Reference placeholder tables in metadata for foreign keys if other team members' models are loaded separately
if "patients" not in db.metadata.tables:
    db.Table("patients", db.metadata, db.Column("id", db.Uuid, primary_key=True), extend_existing=True)
if "doctors" not in db.metadata.tables:
    db.Table("doctors", db.metadata, db.Column("id", db.Uuid, primary_key=True), extend_existing=True)




class Appointment(db.Model):
    __tablename__ = "appointments"

    id = db.Column(db.Uuid, primary_key=True, default=uuid.uuid4)
    patient_id = db.Column(db.Uuid, db.ForeignKey("patients.id"), nullable=False)
    doctor_id = db.Column(db.Uuid, db.ForeignKey("doctors.id"), nullable=False)
    appointment_date = db.Column(db.Date, nullable=False)
    appointment_time = db.Column(db.Time, nullable=False)
    status = db.Column(db.String(50), nullable=False, default="CONFIRMED")
    reason = db.Column(db.Text, nullable=True)
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def to_dict(self):
        return {
            "id": str(self.id) if self.id else None,
            "patient_id": str(self.patient_id) if self.patient_id else None,
            "doctor_id": str(self.doctor_id) if self.doctor_id else None,
            "appointment_date": self.appointment_date.isoformat() if self.appointment_date else None,
            "appointment_time": self.appointment_time.isoformat() if self.appointment_time else None,
            "status": self.status,
            "reason": self.reason,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Ward(db.Model):
    __tablename__ = "wards"

    id = db.Column(db.Uuid, primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(100), nullable=False)
    ward_type = db.Column(db.String(50), nullable=False)  # e.g., General, ICU

    # Relationship to Bed
    beds = db.relationship(
        "Bed",
        back_populates="ward",
        cascade="all, delete-orphan",
        lazy=True,
    )

    def to_dict(self):
        return {
            "id": str(self.id) if self.id else None,
            "name": self.name,
            "ward_type": self.ward_type,
        }


class Bed(db.Model):
    __tablename__ = "beds"

    id = db.Column(db.Uuid, primary_key=True, default=uuid.uuid4)
    ward_id = db.Column(db.Uuid, db.ForeignKey("wards.id"), nullable=False)
    bed_number = db.Column(db.String(50), nullable=False)
    bed_type = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(50), nullable=False, default="AVAILABLE")

    # Relationships
    ward = db.relationship("Ward", back_populates="beds")
    allocations = db.relationship(
        "BedAllocation",
        back_populates="bed",
        cascade="all, delete-orphan",
        lazy=True,
    )

    def to_dict(self):
        return {
            "id": str(self.id) if self.id else None,
            "ward_id": str(self.ward_id) if self.ward_id else None,
            "bed_number": self.bed_number,
            "bed_type": self.bed_type,
            "status": self.status,
        }


class BedAllocation(db.Model):
    __tablename__ = "bed_allocations"

    id = db.Column(db.Uuid, primary_key=True, default=uuid.uuid4)
    bed_id = db.Column(db.Uuid, db.ForeignKey("beds.id"), nullable=False)
    patient_id = db.Column(db.Uuid, db.ForeignKey("patients.id"), nullable=False)
    allocated_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    released_at = db.Column(db.DateTime(timezone=True), nullable=True)
    status = db.Column(db.String(50), nullable=False, default="ACTIVE")

    # Relationship
    bed = db.relationship("Bed", back_populates="allocations")

    def to_dict(self):
        return {
            "id": str(self.id) if self.id else None,
            "bed_id": str(self.bed_id) if self.bed_id else None,
            "patient_id": str(self.patient_id) if self.patient_id else None,
            "allocated_at": self.allocated_at.isoformat() if self.allocated_at else None,
            "released_at": self.released_at.isoformat() if self.released_at else None,
            "status": self.status,
        }
