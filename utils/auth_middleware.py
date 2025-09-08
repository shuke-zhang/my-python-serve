# app/utils/auth_middleware.py
from flask import request, g
from flask_jwt_extended import decode_token
from jwt import ExpiredSignatureError, InvalidTokenError
from utils.response import error_response

WHITE_LIST = { "/api/user/register"}

def jwt_global_auth():
    # 白名单放行
    if request.path in WHITE_LIST:
        return
    print(request.headers.get("Authorization", ""),'查看token')
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token:
        return error_response("未登录或缺少 token", code=401)

    try:
        payload = decode_token(token)
        g.current_user = payload["sub"]  # Flask-JWT-Extended 默认把 identity 存在 sub
    except ExpiredSignatureError:
        return error_response("登录已过期，请重新登录", code=401)
    except InvalidTokenError:
        return error_response("无效 token", code=401)
