"""routes 包:把所有 Blueprint 集中暴露,app.py 一次性注册"""
from .auth import bp as auth_bp
from .docs import bp as docs_bp
from .gold import bp as gold_bp
from .upload import bp as upload_bp

ALL_BLUEPRINTS = [auth_bp, docs_bp, gold_bp, upload_bp]
