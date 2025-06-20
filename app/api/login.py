# app/api/login.py
from flask import Blueprint, request
from flask_jwt_extended import create_access_token
from app.services.login_service import login_user
from utils.response import success_response, error_response
from marshmallow import ValidationError
from app.schemas.login_schema import LoginSchema
from werkzeug.security import generate_password_hash

# ✅ 名字应该叫 auth_bp
auth_bp = Blueprint('auth', __name__, url_prefix='/api')

@auth_bp.route("/login", methods=["POST"])
def login():
    try:
        data = LoginSchema().load(request.get_json())
    except ValidationError as err:
        return error_response("参数校验失败", data=err.messages)
          
    token, err_msg = login_user(data["name"], data["password"])
             
    if err_msg:
        
        return error_response(err_msg, code=401)

    return success_response(msg="登录成功", data={"token": token})
