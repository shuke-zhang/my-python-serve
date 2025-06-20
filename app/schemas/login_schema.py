# 校验层：定义请求/响应格式
from marshmallow import Schema, fields, validate

class LoginSchema(Schema):
    name     = fields.Str(required=True, validate=validate.Length(min=1), error_messages={"required": "用户名不能为空"})
    password = fields.Str(required=True, validate=validate.Length(min=1), error_messages={"required": "密码不能为空"})
