"""
Flask 主入口:8080 端口
- /api/*           业务接口
- /uploads/<file>  上传文件静态访问
- /                Vue 构建产物(frontend/dist) — 兜底返回 index.html(SPA history mode)
"""
import logging
import os

from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS

import config
from db import init_schema, close_conn
from routes import ALL_BLUEPRINTS

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
log = logging.getLogger("app")


def create_app() -> Flask:
    # 将 frontend/dist 设为 static_folder,index.html 为入口
    static_dir = str(config.FRONTEND_DIST) if config.FRONTEND_DIST.exists() else None
    app = Flask(
        __name__,
        static_folder=static_dir,
        static_url_path="",     # 让根目录直接对应 dist
    )

    # 仅在开发期允许跨域,生产期前端与后端同源
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # 注册业务蓝图
    for bp in ALL_BLUEPRINTS:
        app.register_blueprint(bp)

    # 上传目录暴露
    @app.get("/uploads/<path:name>")
    def serve_upload(name: str):
        return send_from_directory(config.UPLOAD_DIR, name)

    # 健康检查
    @app.get("/api/health")
    def health():
        return jsonify(code=0, msg="ok")

    # 前端 history 路由兜底:任何不命中接口与静态文件的路径返回 index.html
    @app.get("/", defaults={"path": ""})
    @app.get("/<path:path>")
    def spa(path: str):
        if static_dir is None:
            return jsonify(
                code=503,
                msg="frontend/dist 不存在,请先在 frontend 下执行 npm run build",
            ), 503
        full = os.path.join(static_dir, path)
        if path and os.path.exists(full):
            return send_from_directory(static_dir, path)
        return send_from_directory(static_dir, "index.html")

    # 数据库连接生命周期
    app.teardown_appcontext(close_conn)

    return app


# 顶层导出供 gunicorn 使用: gunicorn 'app:app'
init_schema()
app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=config.APP_PORT, debug=False, use_reloader=False)
