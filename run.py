import os
import sys
from dotenv import load_dotenv

# ⛳ 关键：加入项目根目录到 sys.path，确保可以导入 app 模块
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 🔁 加载环境变量
env_file = '.env.development' if os.getenv('FLASK_ENV') != 'production' else '.env.production'
load_dotenv(env_file)

# ✅ 导入 create_app
from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
