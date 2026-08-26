from marshmallow import Schema, fields, validate, EXCLUDE


class AllocateBedSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    patient_id = fields.UUID(
        required=True,
        error_messages={"required": "patient_id is required.", "invalid": "Invalid UUID format for patient_id."}
    )
    ward_type = fields.String(
        required=True,
        validate=validate.Length(min=1),
        error_messages={"required": "ward_type is required."}
    )
    bed_type = fields.String(required=False, allow_none=True, load_default=None)


class ReleaseBedSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    bed_id = fields.UUID(
        required=False,
        error_messages={"invalid": "Invalid UUID format for bed_id."}
    )
    patient_id = fields.UUID(
        required=False,
        error_messages={"invalid": "Invalid UUID format for patient_id."}
    )


class CreateWardSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    name = fields.String(
        required=True,
        validate=validate.Length(min=1, max=100),
        error_messages={"required": "name is required."}
    )
    ward_type = fields.String(
        required=True,
        validate=validate.Length(min=1, max=50),
        error_messages={"required": "ward_type is required."}
    )


class CreateBedSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    ward_id = fields.UUID(
        required=True,
        error_messages={"required": "ward_id is required.", "invalid": "Invalid UUID format for ward_id."}
    )
    bed_number = fields.String(
        required=True,
        validate=validate.Length(min=1, max=50),
        error_messages={"required": "bed_number is required."}
    )
    bed_type = fields.String(
        required=True,
        validate=validate.Length(min=1, max=50),
        error_messages={"required": "bed_type is required."}
    )
    status = fields.String(
        load_default="AVAILABLE",
        validate=validate.OneOf(["AVAILABLE", "OCCUPIED", "MAINTENANCE", "RESERVED"])
    )


class WardResponseSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.UUID()
    name = fields.String()
    ward_type = fields.String()


class BedResponseSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.UUID()
    ward_id = fields.UUID()
    bed_number = fields.String()
    bed_type = fields.String()
    status = fields.String()


class BedAllocationResponseSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.UUID()
    bed_id = fields.UUID()
    patient_id = fields.UUID()
    allocated_at = fields.DateTime()
    released_at = fields.DateTime(allow_none=True)
    status = fields.String()


# Pre-instantiated schema singletons for convenient import
allocate_bed_schema = AllocateBedSchema()
release_bed_schema = ReleaseBedSchema()
create_ward_schema = CreateWardSchema()
create_bed_schema = CreateBedSchema()
ward_response_schema = WardResponseSchema()
wards_response_schema = WardResponseSchema(many=True)
bed_response_schema = BedResponseSchema()
beds_response_schema = BedResponseSchema(many=True)
bed_allocation_response_schema = BedAllocationResponseSchema()
bed_allocations_response_schema = BedAllocationResponseSchema(many=True)
