import os
from pathlib import Path

class Settings:
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "zhangenjian123..")
    DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
    DB_PORT = os.getenv("DB_PORT", "3307")
    DB_NAME = os.getenv("DB_NAME", "shuke")

    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4",
    )

    STORAGE_DIR = Path(os.getenv("STORAGE_DIR", "./storage")).resolve()
    TMP_DIR = Path(os.getenv("TMP_DIR", "./tmp")).resolve()
    CHUNK_SIZE = 1024 * 1024 * 8  # 8MB

# 确保目录存在
Settings.STORAGE_DIR.mkdir(parents=True, exist_ok=True)
Settings.TMP_DIR.mkdir(parents=True, exist_ok=True)
