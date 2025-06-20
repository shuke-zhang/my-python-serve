from flask import Blueprint, request
from app.models.user import User
from app.models import db
from utils.response import success_response, error_response
from werkzeug.security import check_password_hash

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.json
    name = data.get('name')
    password = data.get('password')

    if not name or not password:
        return error_response("用户名或密码不能为空")

    user = User.query.filter_by(name=name).first()
    if not user:
        return error_response("用户不存在")

    if not check_password_hash(user.password, password):
        return error_response("密码错误")

    # 此处可返回 token 或用户信息（未集成 JWT 就简单返回 user info）
    return success_response({
        "id": user.id,
        "name": user.name,
        "nick_name": user.nick_name
    }, msg="登录成功")
