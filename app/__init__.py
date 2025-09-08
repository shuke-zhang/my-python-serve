from flask import Flask, request, make_response
from app.api import register_blueprints
from app.models import db
from config import load_config
from flask_jwt_extended import JWTManager
from app.api.volc_socket import init_socketio
from flask_socketio import SocketIO
from flask_cors import CORS

jwt = JWTManager()
socketio: SocketIO = SocketIO(
    cors_allowed_origins="*",   # SocketIO 允许任何来源
    async_mode="threading",
    logger=False,
    engineio_logger=False,
)

def create_app():
    app = Flask(__name__)
    app.config.update(load_config())

    # 1) 初始化扩展
    db.init_app(app)
    jwt.init_app(app)
    socketio.init_app(app)

    # 2) 启用 CORS，origins 写 * 就行
    CORS(
        app,
        resources={r"/api/*": {"origins": "*"}},
        supports_credentials=True,  # 允许 cookie / session
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=[
            "Content-Type",
            "Authorization",
            "X-Requested-With",
            "X-Token",
            "x-token",
            "token",
        ],
        expose_headers=["Content-Disposition"],
        max_age=86400,
    )

    # 3) 动态回写真实 Origin（关键）
    @app.after_request
    def apply_cors(response):
        origin = request.headers.get("Origin")
        if origin:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Vary"] = "Origin"
        return response

    # 4) 注册蓝图
    register_blueprints(app)

    # 5) 初始化 socket.io 事件
    init_socketio(socketio)

    return app
