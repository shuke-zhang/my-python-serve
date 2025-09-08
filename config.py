import os
import uuid
from dotenv import load_dotenv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
VOLC_BASE_URL = "wss://openspeech.bytedance.com/api/v3/realtime/dialogue"
VOLC_APP_ID = os.getenv("VOLC_APP_ID", "")
VOLC_ACCESS_KEY = os.getenv("VOLC_ACCESS_KEY", "")
VOLC_RESOURCE_ID = os.getenv("VOLC_RESOURCE_ID", "volc.speech.dialog")
VOLC_APP_KEY = os.getenv("VOLC_APP_KEY", "PlgvMymc7f3tQnJ6")

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
        "SECRET_KEY": os.getenv("SECRET_KEY", "fallback-secret"),  # ⭐ 全局密钥
        "JSON_AS_ASCII": False,
    }

def build_ws_headers() -> dict:
    return {
        "X-Api-App-ID": VOLC_APP_ID,
        "X-Api-Access-Key": VOLC_ACCESS_KEY,
        "X-Api-Resource-Id": VOLC_RESOURCE_ID,
        "X-Api-App-Key": VOLC_APP_KEY,
        "X-Api-Connect-Id": str(uuid.uuid4())
    }