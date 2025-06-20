from app.api.users import user_bp
from app.api.login import login_bp

def register_blueprints(app):
    # 注册用户模块路由
    app.register_blueprint(user_bp)
    app.register_blueprint(login_bp)
