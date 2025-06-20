# 路由层：只负责接收参数、调用 service、返回响应
from flask import Blueprint, request
from marshmallow import ValidationError
from utils.response import success_response, error_response
from app.schemas.login_schema import LoginSchema     
from app.services.login_service import login_user    
login_bp = Blueprint("login", __name__, url_prefix="/api")

@login_bp.route("/login", methods=["POST"])
def login():
    try:
        # 参数校验
        data = LoginSchema().load(request.get_json())
    except ValidationError as err:
        return error_response("参数校验失败", data=err.messages)

    # 业务处理
    token, err_msg = login_user(data["name"], data["password"])
    if err_msg:
        return error_response(err_msg, code=401)

    return success_response({"token": token}, msg="登录成功")
