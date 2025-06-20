import os
from dotenv import load_dotenv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

def load_config():
    # 加载对应环境变量文件
    env_file = ".env.production" if os.getenv("FLASK_ENV") == "production" else ".env.development"
    load_dotenv(BASE_DIR / env_file)

    # 拼接数据库连接字符串
    db_uri = (
        f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
        f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    )

    return {
        "SQLALCHEMY_DATABASE_URI": db_uri,
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        "SECRET_KEY": os.getenv("SECRET_KEY", "fallback-secret"),
        "JSON_AS_ASCII": False,
    }
