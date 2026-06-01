"""登录接口"""
from flask import Blueprint, request, jsonify, g
from werkzeug.security import check_password_hash

from db import get_conn
from auth import create_token, login_required

bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@bp.post("/login")
def login():
    """
    POST /api/auth/login
    body: { "username": "...", "password": "..." }
    返回: { code, msg, data: { token, username } }
    """
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    if not username or not password:
        return jsonify(code=400, msg="用户名/密码不能为空"), 400

    row = get_conn().execute(
        "SELECT id, username, password_hash FROM admin WHERE username=?",
        (username,),
    ).fetchone()
    if not row or not check_password_hash(row["password_hash"], password):
        return jsonify(code=401, msg="用户名或密码错误"), 401

    token = create_token(row["id"], row["username"])
    return jsonify(code=0, msg="ok", data={"token": token, "username": row["username"]})


@bp.get("/me")
@login_required
def me():
    """GET /api/auth/me  当前登录态校验,前端启动时调用"""
    return jsonify(code=0, msg="ok", data={"username": g.user.get("username")})
