def format_bed_response(bed_data: dict, requested_type: str = None) -> str:
    """Formats bed availability results into conversational text."""
    available_count = bed_data.get("available_count", 0)
    bed_type = bed_data.get("bed_type") or requested_type or "standard"
    ward = bed_data.get("ward")

    if available_count > 0:
        ward_info = f" in {ward}" if ward else ""
        return f"We currently have {available_count} {bed_type} bed(s) available{ward_info}."
    return f"Sorry, there are currently no {bed_type} beds available. Please check back later or visit emergency triage."


def format_doctor_availability_response(doc_data: dict, entities: dict) -> str:
    """Formats doctor schedule lookup."""
    doctor_name = doc_data.get("doctor_name") or entities.get("doctor_name") or "The doctor"
    slots = doc_data.get("available_slots", [])
    
    if slots:
        slots_str = ", ".join(slots[:3])
        return f"Dr. {doctor_name} is available on {entities.get('date', 'the requested date')}. Available slots: {slots_str}."
    return f"Dr. {doctor_name} has no available slots for {entities.get('date', 'the selected date')}."


def format_booking_response(booking_result: dict) -> str:
    """Formats appointment booking confirmation."""
    if booking_result.get("status") == "CONFIRMED":
        return (
            f"Your appointment has been confirmed with Dr. {booking_result.get('doctor_name')} "
            f"for {booking_result.get('date')} at {booking_result.get('time')} "
            f"(Booking ID: {booking_result.get('appointment_id', 'N/A')})."
        )
    return f"Could not book the appointment: {booking_result.get('error', 'Selected slot is no longer available')}."


def format_cancellation_response(cancel_result: dict) -> str:
    """Formats appointment cancellation status."""
    if cancel_result.get("success"):
        return f"Your appointment (ID: {cancel_result.get('appointment_id')}) has been successfully cancelled."
    return f"Unable to cancel appointment: {cancel_result.get('error', 'Appointment not found')}."


def format_unknown_response() -> str:
    """Fallback message when intent is not recognized."""
    return (
        "I'm sorry, I didn't quite understand that. I can help you check bed availability, "
        "look up doctor schedules, or book/cancel an appointment."
    )
