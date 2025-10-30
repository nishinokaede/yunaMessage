from pathlib import Path

# 基础配置
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
MESSAGE_DIR = DATA_DIR / "messages"
DB_PATH = DATA_DIR / "app.db"

# 文件服务器基础URL（可按需改为你的域名）
# 需求指定：file.densu.cc/data/messages/{membername}/{file}
# 如需在本机访问，可改为 http://localhost:8000
FILE_BASE_URL = "http://file.densu.cc"

# 目录确保存在
DATA_DIR.mkdir(parents=True, exist_ok=True)
MESSAGE_DIR.mkdir(parents=True, exist_ok=True)

# 定时任务配置说明（具体在main中配置CronTrigger）
# gettoken: 0-7不执行；8-23每10分钟
# getmessage: 0-7不执行；8-19每小时；20-23每10分钟