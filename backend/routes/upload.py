"""
文件上传(主要用于 Markdown 内嵌图片)。
- POST /api/upload  multipart/form-data, field=file
- 静态访问:/uploads/<filename> (在 app.py 中通过 add_url_rule 暴露)
"""
import os
import uuid
from pathlib import Path

from flask import Blueprint, request, jsonify

import config
from auth import login_required

bp = Blueprint("upload", __name__, url_prefix="/api/upload")


@bp.post("")
@login_required
def upload_image():
    if "file" not in request.files:
        return jsonify(code=400, msg="缺少 file 字段"), 400
    f = request.files["file"]
    if not f.filename:
        return jsonify(code=400, msg="文件名为空"), 400

    ext = Path(f.filename).suffix.lower()
    if ext not in config.ALLOWED_IMAGE_EXT:
        return jsonify(code=400, msg=f"仅支持图片格式: {','.join(config.ALLOWED_IMAGE_EXT)}"), 400

    # 检查大小(避免读完才报错,先 seek 到末尾)
    f.stream.seek(0, os.SEEK_END)
    size = f.stream.tell()
    f.stream.seek(0)
    if size > config.MAX_UPLOAD_BYTES:
        return jsonify(
            code=400,
            msg=f"文件超过 {config.MAX_UPLOAD_BYTES // 1024 // 1024} MB",
        ), 400

    # 用 uuid 重命名,避免中文/重名问题
    new_name = f"{uuid.uuid4().hex}{ext}"
    target = Path(config.UPLOAD_DIR) / new_name
    f.save(str(target))

    url = f"/uploads/{new_name}"
    # md-editor-v3 默认使用 data.url 作为图片地址
    return jsonify(code=0, msg="ok", data={"url": url, "name": new_name, "size": size})
