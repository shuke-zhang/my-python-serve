# app/schemas/user_schema.py
from marshmallow import Schema, fields, validate, ValidationError

# ✅ 注册时用的 schema（只校验输入）
class UserSchema(Schema):
    name = fields.Str(required=True, validate=validate.Length(min=1),
                      error_messages={"required": "用户名不能为空"})
    password = fields.Str(required=True, validate=validate.Length(min=6),
                          error_messages={"required": "密码不能为空", "invalid": "密码至少为6位"})
    nick_name = fields.Str()
    email = fields.Str(validate=validate.Email(error="邮箱格式不正确"))
    phone = fields.Str()
    id_card = fields.Str(validate=validate.Length(max=18, error="身份证号不能超过18位"))
    sex = fields.Integer(
        validate=validate.OneOf([1, 2], error="性别只能是 1（男） 或 2（女）"),
        error_messages={"invalid": "性别必须是整数 1 或 2"}
    )
    avatar = fields.Str()
    remark = fields.Str()
    status = fields.Str()
def load_and_validate(schema: Schema, json_data: dict):
    """
    封装后的通用加载和校验函数。
    若校验失败，抛出格式化后的异常字符串。
    """
    try:
        return schema.load(json_data)
    except ValidationError as err:
        # 格式化错误信息
        all_msgs = []
        for field, messages in err.messages.items():
            for msg in messages:
                all_msgs.append(f"{field}: {msg}")
        msg = "；".join(all_msgs)
        raise ValueError(f"参数校验失败：{msg}")

# ✅ 实例化
user_schema = UserSchema()
users_schema = UserSchema(many=True)
