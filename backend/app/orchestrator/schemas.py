from marshmallow import Schema, fields


class AssistantRequestSchema(Schema):
    message = fields.String(required=True)


class AssistantResponseSchema(Schema):
    success = fields.Boolean(required=True)
    intent = fields.String(required=True)
    data = fields.Dict(allow_none=True)
    message = fields.String(required=True)
    next_action = fields.String(allow_none=True)
