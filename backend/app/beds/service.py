import uuid
from datetime import datetime, timezone
from typing import Optional, Tuple, List, Dict, Any
from sqlalchemy import func

from app.extensions import db
from app.models import Ward, Bed, BedAllocation


def get_bed_availability(ward_type: Optional[str] = None) -> Tuple[Dict[str, Any], str, Optional[str]]:
    """
    Calculates overall bed availability and filters by ward type if provided.
    Directly counts total beds and available beds from the database.
    """
    try:
        bed_query = Bed.query.join(Ward)

        if ward_type and ward_type.strip():
            clean_ward = ward_type.strip()
            bed_query = bed_query.filter(
                (func.lower(Ward.ward_type) == func.lower(clean_ward)) |
                (func.lower(Ward.name) == func.lower(clean_ward))
            )

        total_beds = bed_query.count()
        available_beds = bed_query.filter(Bed.status == "AVAILABLE").count()
        occupied_beds = bed_query.filter(Bed.status == "OCCUPIED").count()
        maintenance_beds = bed_query.filter(Bed.status == "MAINTENANCE").count()
        reserved_beds = bed_query.filter(Bed.status == "RESERVED").count()

        beds = bed_query.all()
        beds_data = []
        for b in beds:
            item = b.to_dict()
            item["ward_name"] = b.ward.name if b.ward else None
            item["ward_type"] = b.ward.ward_type if b.ward else None
            beds_data.append(item)

        data = {
            "ward_filter": ward_type.strip() if ward_type else None,
            "total_beds": total_beds,
            "available_beds": available_beds,
            "occupied_beds": occupied_beds,
            "maintenance_beds": maintenance_beds,
            "reserved_beds": reserved_beds,
            "beds": beds_data
        }

        return data, "Bed availability retrieved successfully.", None
    except Exception as e:
        return {}, f"Database error querying bed availability: {str(e)}", "DATABASE_ERROR"


def allocate_bed(
    patient_id: Any,
    ward_type: str,
    bed_type: Optional[str] = None
) -> Tuple[Optional[Dict[str, Any]], str, Optional[str]]:
    """
    Finds an AVAILABLE bed for the requested ward type, marks it OCCUPIED,
    and creates an active BedAllocation record.

    If no beds are free, returns a BED_UNAVAILABLE error.
    """
    try:
        p_uuid = uuid.UUID(str(patient_id)) if not isinstance(patient_id, uuid.UUID) else patient_id
    except (ValueError, TypeError):
        return None, "Invalid patient_id UUID format.", "INVALID_ID"

    if not ward_type or not ward_type.strip():
        return None, "ward_type is required.", "VALIDATION_ERROR"

    clean_ward = ward_type.strip()

    try:
        # Query for an AVAILABLE bed matching the ward type
        bed_query = Bed.query.join(Ward).filter(
            (func.lower(Ward.ward_type) == func.lower(clean_ward)) |
            (func.lower(Ward.name) == func.lower(clean_ward)),
            Bed.status == "AVAILABLE"
        )

        if bed_type and bed_type.strip():
            bed_query = bed_query.filter(func.lower(Bed.bed_type) == func.lower(bed_type.strip()))

        bed = bed_query.with_for_update().first() if db.engine.name == "postgresql" else bed_query.first()

        if not bed:
            return None, f"No available beds in ward type '{ward_type}'.", "BED_UNAVAILABLE"

        # Update bed status to OCCUPIED
        bed.status = "OCCUPIED"

        # Create BedAllocation record
        allocation = BedAllocation(
            bed_id=bed.id,
            patient_id=p_uuid,
            allocated_at=datetime.now(timezone.utc),
            status="ACTIVE"
        )
        db.session.add(allocation)
        db.session.commit()

        result = {
            "allocation": allocation.to_dict(),
            "bed": {
                **bed.to_dict(),
                "ward_name": bed.ward.name if bed.ward else None,
                "ward_type": bed.ward.ward_type if bed.ward else None
            }
        }

        return result, "Bed allocated successfully.", None
    except Exception as e:
        db.session.rollback()
        return None, f"Database error allocating bed: {str(e)}", "DATABASE_ERROR"


def release_bed(bed_id: Any) -> Tuple[Optional[Dict[str, Any]], str, Optional[str]]:
    """
    Checks that the bed is OCCUPIED, closes its active BedAllocation record,
    and sets the bed status back to AVAILABLE.
    """
    try:
        b_uuid = uuid.UUID(str(bed_id)) if not isinstance(bed_id, uuid.UUID) else bed_id
    except (ValueError, TypeError):
        return None, "Invalid bed ID format.", "INVALID_ID"

    try:
        bed = db.session.get(Bed, b_uuid)
        if not bed:
            return None, "Bed not found.", "BED_NOT_FOUND"

        if bed.status != "OCCUPIED":
            return None, f"Bed {bed.bed_number} is not currently occupied (status: {bed.status}).", "BED_NOT_OCCUPIED"

        # Close the active allocation
        active_allocation = BedAllocation.query.filter_by(
            bed_id=bed.id,
            status="ACTIVE"
        ).order_by(BedAllocation.allocated_at.desc()).first()

        if active_allocation:
            active_allocation.status = "RELEASED"
            active_allocation.released_at = datetime.now(timezone.utc)

        # Set bed status back to AVAILABLE
        bed.status = "AVAILABLE"
        db.session.commit()

        result = {
            "bed": {
                **bed.to_dict(),
                "ward_name": bed.ward.name if bed.ward else None,
                "ward_type": bed.ward.ward_type if bed.ward else None
            },
            "allocation": active_allocation.to_dict() if active_allocation else None
        }

        return result, "Bed released successfully.", None
    except Exception as e:
        db.session.rollback()
        return None, f"Database error releasing bed: {str(e)}", "DATABASE_ERROR"


def get_bed_by_id(bed_id: Any) -> Tuple[Optional[Dict[str, Any]], str, Optional[str]]:
    """
    Retrieves details of a specific bed including ward info and any active allocation.
    """
    try:
        b_uuid = uuid.UUID(str(bed_id)) if not isinstance(bed_id, uuid.UUID) else bed_id
    except (ValueError, TypeError):
        return None, "Invalid bed ID format.", "INVALID_ID"

    try:
        bed = db.session.get(Bed, b_uuid)
        if not bed:
            return None, "Bed not found.", "BED_NOT_FOUND"

        active_allocation = BedAllocation.query.filter_by(
            bed_id=bed.id,
            status="ACTIVE"
        ).first()

        bed_dict = bed.to_dict()
        bed_dict["ward"] = bed.ward.to_dict() if bed.ward else None
        bed_dict["active_allocation"] = active_allocation.to_dict() if active_allocation else None

        return bed_dict, "Bed retrieved successfully.", None
    except Exception as e:
        return None, f"Database error retrieving bed: {str(e)}", "DATABASE_ERROR"
