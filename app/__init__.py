from flask import Flask
from app.api import register_blueprints
from app.models import db
from config import load_config  # ✅ 改为从 config 加载
from flask_jwt_extended import JWTManager
from utils.auth_middleware import jwt_global_auth
from app.api.volc_socket import init_socketio
from flask_socketio import SocketIO

jwt = JWTManager()
socketio: SocketIO = SocketIO(
    cors_allowed_origins="*",
    async_mode="threading",  # 没装 eventlet 可改为 "threading"
    logger=False,
    engineio_logger=False
)

def create_app():
    app = Flask(__name__)
    app.config.update(load_config()) 
    db.init_app(app)
    jwt.init_app(app)
    socketio.init_app(app)
    init_socketio(socketio)
    register_blueprints(app)
 # ② 注册全局 before_request 中间件
    app.before_request(jwt_global_auth)
    return app
