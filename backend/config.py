"""
全局配置:从 .env 加载环境变量,集中暴露常量供其它模块使用。
所有可调参数都走环境变量,避免在代码里硬编码秘钥。
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# 项目根目录(backend/)
BASE_DIR = Path(__file__).resolve().parent

# 加载 .env(若不存在则使用系统环境变量)
load_dotenv(BASE_DIR / ".env")


def _int(key: str, default: int) -> int:
    """读取整数环境变量,失败回退到默认值"""
    try:
        return int(os.getenv(key, default))
    except (TypeError, ValueError):
        return default


# ---------- 端口 ----------
APP_PORT = _int("APP_PORT", 8080)
MONITOR_PORT = _int("MONITOR_PORT", 9000)

# ---------- 管理员 ----------
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

# ---------- JWT ----------
JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-please-change")
JWT_ALG = "HS256"
JWT_EXPIRE_DAYS = _int("JWT_EXPIRE_DAYS", 7)

# ---------- 数据库 ----------
DB_PATH = os.getenv("DB_PATH", "data.db")
if not os.path.isabs(DB_PATH):
    DB_PATH = str(BASE_DIR / DB_PATH)

# ---------- 上传 ----------
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
if not os.path.isabs(UPLOAD_DIR):
    UPLOAD_DIR = str(BASE_DIR / UPLOAD_DIR)
os.makedirs(UPLOAD_DIR, exist_ok=True)
MAX_UPLOAD_BYTES = _int("MAX_UPLOAD_BYTES", 5 * 1024 * 1024)
ALLOWED_IMAGE_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"}

# ---------- 金价 ----------
GOLD_PRODUCT_CODE = os.getenv("GOLD_PRODUCT_CODE", "Au99.99")
GOLD_POLL_INTERVAL = _int("GOLD_POLL_INTERVAL", 300)
JD_GOLD_API = os.getenv(
    "JD_GOLD_API",
    "https://ms.jr.jd.com/gw/generic/hj/h5/m/latestPrice",
)

# ---------- 前端构建产物路径(由 Flask 静态托管) ----------
FRONTEND_DIST = BASE_DIR.parent / "frontend" / "dist"
