from marshmallow import Schema, fields, validate, ValidationError

class UploadInitSchema(Schema):
    filename = fields.Str(required=True, validate=validate.Length(min=1))
    expected_size = fields.Integer(required=False)
    expected_sha256 = fields.Str(required=False)

class UploadCommitSchema(Schema):
    expected_size = fields.Integer(required=False)
    expected_sha256 = fields.Str(required=False)
    content_type = fields.Str(required=False)
    note = fields.Str(required=False)

def load_and_validate(schema: Schema, json_data: dict):
    try:
        return schema.load(json_data or {})
    except ValidationError as err:
        all_msgs = []
        for field, messages in err.messages.items():
            for msg in messages:
                all_msgs.append(f"{field}: {msg}")
        msg = "；".join(all_msgs)
        raise ValueError(f"参数校验失败：{msg}")
