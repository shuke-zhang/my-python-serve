from marshmallow import Schema, fields, validate

class UserSchema(Schema):
    id = fields.Int(dump_only=True)
    user_id = fields.Int()
    name = fields.Str(required=True, validate=validate.Length(min=1))
    nick_name = fields.Str()
    email = fields.Str()
    phone = fields.Str()
    id_card = fields.Str()
    sex = fields.Str()
    avatar = fields.Str()
    password = fields.Str(required=True)
    remark = fields.Str()
    status = fields.Int()

user_schema = UserSchema()
users_schema = UserSchema(many=True)
