"""
金价接口:
- GET /api/gold/latest        最新一条
- GET /api/gold/history       历史(?range=1h|24h|7d|30d|all)
- GET /api/gold/config        当前监控配置
- PUT /api/gold/config        修改监控配置(需登录) -> 修改后通知 monitor 进程重新调度(可选)
- POST /api/gold/refresh      手动触发一次拉取(需登录)
"""
from datetime import datetime, timedelta, timezone

from flask import Blueprint, request, jsonify

from db import get_conn
from auth import login_required
from services.jd_gold import fetch_and_save

bp = Blueprint("gold", __name__, url_prefix="/api/gold")


# 时间区间 -> 起始 datetime
_RANGE_MAP = {
    "1h": timedelta(hours=1),
    "24h": timedelta(hours=24),
    "7d": timedelta(days=7),
    "30d": timedelta(days=30),
}


@bp.get("/latest")
def latest():
    row = get_conn().execute(
        "SELECT id, product_code, price, fetched_at FROM gold_price "
        "ORDER BY fetched_at DESC LIMIT 1"
    ).fetchone()
    return jsonify(code=0, msg="ok", data=dict(row) if row else None)


@bp.get("/history")
def history():
    rng = request.args.get("range", "24h")
    conn = get_conn()
    if rng == "all":
        rows = conn.execute(
            "SELECT id, price, fetched_at FROM gold_price ORDER BY fetched_at ASC"
        ).fetchall()
    else:
        delta = _RANGE_MAP.get(rng, _RANGE_MAP["24h"])
        since = (datetime.now(timezone.utc) - delta).strftime("%Y-%m-%d %H:%M:%S")
        rows = conn.execute(
            """SELECT id, price, fetched_at FROM gold_price
               WHERE fetched_at >= ? ORDER BY fetched_at ASC""",
            (since,),
        ).fetchall()
    return jsonify(
        code=0,
        msg="ok",
        data={"range": rng, "items": [dict(r) for r in rows]},
    )


@bp.get("/config")
def get_config():
    row = get_conn().execute(
        "SELECT * FROM gold_config WHERE id=1"
    ).fetchone()
    return jsonify(code=0, msg="ok", data=dict(row) if row else None)


@bp.put("/config")
@login_required
def update_config():
    """
    body: { product_code?, poll_interval_sec?, enabled? }
    监控进程会每分钟回读配置(简单方案,无需 IPC)。
    """
    data = request.get_json(silent=True) or {}
    fields = []
    params: list = []
    if "product_code" in data:
        fields.append("product_code=?")
        params.append(str(data["product_code"]).strip() or "Au99.99")
    if "poll_interval_sec" in data:
        try:
            v = int(data["poll_interval_sec"])
            v = max(30, min(86400, v))   # 30s ~ 1d
        except (TypeError, ValueError):
            return jsonify(code=400, msg="poll_interval_sec 必须为整数"), 400
        fields.append("poll_interval_sec=?")
        params.append(v)
    if "enabled" in data:
        fields.append("enabled=?")
        params.append(1 if data["enabled"] else 0)
    if not fields:
        return jsonify(code=400, msg="无可更新字段"), 400

    fields.append("updated_at=CURRENT_TIMESTAMP")
    sql = "UPDATE gold_config SET " + ", ".join(fields) + " WHERE id=1"
    conn = get_conn()
    conn.execute(sql, params)
    conn.commit()
    return jsonify(code=0, msg="ok")


@bp.post("/refresh")
@login_required
def refresh_now():
    """手动触发一次京东金价拉取(同步执行,适合调试)"""
    try:
        result = fetch_and_save()
        return jsonify(code=0, msg="ok", data=result)
    except Exception as e:    # noqa: BLE001
        return jsonify(code=500, msg=f"拉取失败: {e}"), 500
