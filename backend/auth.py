"""
JWT 鉴权工具。
- create_token(): 登录成功后签发
- decode_token(): 解析并校验过期
- login_required: Flask 装饰器,挂在需要鉴权的路由上
"""
from datetime import datetime, timedelta, timezone
from functools import wraps

import jwt
from flask import request, jsonify, g

import config


def create_token(user_id: int, username: str) -> str:
    """签发 JWT。payload 仅包含必要信息,过期时间由 config.JWT_EXPIRE_DAYS 控制。"""
    now = datetime.now(timezone.utc)
    payload = {
        "uid": user_id,
        "username": username,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(days=config.JWT_EXPIRE_DAYS)).timestamp()),
    }
    return jwt.encode(payload, config.JWT_SECRET, algorithm=config.JWT_ALG)


def decode_token(token: str) -> dict | None:
    """解析 JWT,失败返回 None(包括过期、签名错误等)。"""
    try:
        return jwt.decode(token, config.JWT_SECRET, algorithms=[config.JWT_ALG])
    except jwt.PyJWTError:
        return None


def login_required(fn):
    """
    装饰器:校验请求头 Authorization: Bearer <token>。
    校验通过后把 payload 放到 flask.g.user。
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return jsonify(code=401, msg="未登录或缺少 Authorization 头"), 401
        token = auth[7:].strip()
        payload = decode_token(token)
        if payload is None:
            return jsonify(code=401, msg="登录已过期或 token 无效"), 401
        g.user = payload
        return fn(*args, **kwargs)

    return wrapper
