import jwt
import datetime
from flask import request, current_app, g
from functools import wraps
from utils.response import error_response


def generate_token(user_id, expire_minutes=60):
    payload = {
        "user_id": user_id,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=expire_minutes)
    }
    secret = current_app.config.get("SECRET_KEY", "fallback-secret")
    return jwt.encode(payload, secret, algorithm="HS256")


def decode_token(token):
    secret = current_app.config["SECRET_KEY"]
    return jwt.decode(token, secret, algorithms=["HS256"])


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].replace("Bearer ", "")
        if not token:
            return error_response("未登录或缺少 token", code=401)
        try:
            payload = decode_token(token)
            g.current_user = payload["user_id"]
        except jwt.ExpiredSignatureError:
            return error_response("登录过期", code=401)
        except jwt.InvalidTokenError:
            return error_response("无效 token", code=401)
        return f(*args, **kwargs)
    return decorated
