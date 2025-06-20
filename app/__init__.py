from flask import Flask
from app.api import register_blueprints
from app.models import db
from config import load_config  # ✅ 改为从 config 加载

def create_app():
    app = Flask(__name__)
    app.config.from_mapping(load_config())  # ✅ 从 config.py 加载配置

    db.init_app(app)
    register_blueprints(app)

    return app
