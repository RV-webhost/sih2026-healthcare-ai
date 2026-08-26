from marshmallow import Schema, fields, validate, pre_load, EXCLUDE


class CreateAppointmentSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    patient_id = fields.UUID(
        required=True,
        error_messages={"required": "patient_id is required.", "invalid": "Invalid UUID format for patient_id."}
    )
    doctor_id = fields.UUID(
        required=True,
        error_messages={"required": "doctor_id is required.", "invalid": "Invalid UUID format for doctor_id."}
    )
    appointment_date = fields.Date(
        required=True,
        error_messages={"required": "appointment_date (or date) is required.", "invalid": "Invalid date format. Use YYYY-MM-DD."}
    )
    appointment_time = fields.Time(
        required=True,
        error_messages={"required": "appointment_time (or time) is required.", "invalid": "Invalid time format. Use HH:MM or HH:MM:SS."}
    )
    status = fields.String(
        load_default="CONFIRMED",
        validate=validate.OneOf(["CONFIRMED", "PENDING", "CANCELLED", "COMPLETED"])
    )
    reason = fields.String(allow_none=True, load_default=None)

    @pre_load
    def normalize_aliases(self, data, **kwargs):
        if not isinstance(data, dict):
            return data
        payload = data.copy()
        # Support "date" alias for "appointment_date"
        if "date" in payload and "appointment_date" not in payload:
            payload["appointment_date"] = payload.pop("date")
        # Support "time" alias for "appointment_time"
        if "time" in payload and "appointment_time" not in payload:
            payload["appointment_time"] = payload.pop("time")
        return payload


class UpdateAppointmentSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    appointment_date = fields.Date(
        required=False,
        error_messages={"invalid": "Invalid date format. Use YYYY-MM-DD."}
    )
    appointment_time = fields.Time(
        required=False,
        error_messages={"invalid": "Invalid time format. Use HH:MM or HH:MM:SS."}
    )
    status = fields.String(
        required=False,
        validate=validate.OneOf(["CONFIRMED", "PENDING", "CANCELLED", "COMPLETED"])
    )
    reason = fields.String(allow_none=True, required=False)

    @pre_load
    def normalize_aliases(self, data, **kwargs):
        if not isinstance(data, dict):
            return data
        payload = data.copy()
        if "date" in payload and "appointment_date" not in payload:
            payload["appointment_date"] = payload.pop("date")
        if "time" in payload and "appointment_time" not in payload:
            payload["appointment_time"] = payload.pop("time")
        return payload


class AppointmentResponseSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.UUID()
    patient_id = fields.UUID()
    doctor_id = fields.UUID()
    appointment_date = fields.Date()
    appointment_time = fields.Time()
    status = fields.String()
    reason = fields.String(allow_none=True)
    created_at = fields.DateTime()
    updated_at = fields.DateTime()


# Pre-instantiated schema singletons for convenient import
create_appointment_schema = CreateAppointmentSchema()
update_appointment_schema = UpdateAppointmentSchema()
appointment_response_schema = AppointmentResponseSchema()
appointments_response_schema = AppointmentResponseSchema(many=True)
