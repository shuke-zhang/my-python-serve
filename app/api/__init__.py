from app.api.users import user_bp

def register_blueprints(app):
    # 注册用户模块路由
    app.register_blueprint(user_bp)
