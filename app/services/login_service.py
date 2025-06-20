# 业务层：聚合模型、工具、持久化，保持路由层简洁
from app.models.user import User
from app.models.login_log import LoginLog
from app.models import db
from utils.auth import generate_token
from werkzeug.security import check_password_hash
from flask import request

def login_user(name: str, password: str):
    """
    验证账号密码 → 生成 JWT → 写登录日志
    :return: (token, error_msg)  error_msg 为 None 表示成功
    """
    user = User.query.filter_by(name=name).first()
    if not user:
        return None, "用户不存在"

    # 若已做加密存储
    if not check_password_hash(user.password, password):
        return None, "密码错误"

    # 生成 JWT
    token = generate_token(user.user_id)

    # 记录登录日志
    log = LoginLog(user_id=user.user_id, ip=request.remote_addr)
    db.session.add(log)
    db.session.commit()

    return token, None
