from app.api.users import user_bp
from app.api.login import auth_bp

def register_blueprints(app):
    # 注册用户模块路由
    app.register_blueprint(user_bp)
    app.register_blueprint(auth_bp)
