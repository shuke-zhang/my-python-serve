from app.models.user import User
from app.models.login_log import LoginLog
from app.models import db
from werkzeug.security import check_password_hash
from flask import request, current_app
import jwt
import datetime

def generate_token(user_id, expire_minutes=60):
    """
    生成 JWT Token
    """
    payload = {
        "sub": user_id,  # JWT 中的标准字段，代表主体 subject
        "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=expire_minutes)
    }
    secret = current_app.config.get("SECRET_KEY", "fallback-secret")
    return jwt.encode(payload, secret, algorithm="HS256")


def login_user(name: str, password: str):
    """
    处理用户登录：
    - 验证账号密码
    - 生成 JWT Token
    - 写入登录日志
    :return: (token, error_msg)；成功时 error_msg 为 None
    """
    user = User.query.filter_by(name=name).first()
    print("查看密码",name,user.password,password,'------',check_password_hash(user.password, password))
    print("检查",check_password_hash(user.password, '123456'))
    if not user:
        return None, "用户不存在"
        p
    if not check_password_hash(user.password, password):
        return None, "密码错误"

    token = generate_token(user.user_id)

    try:
        log = LoginLog(user_id=user.user_id, ip=request.remote_addr)
        db.session.add(log)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return None, f"登录日志写入失败：{str(e)}"

    return token, None
