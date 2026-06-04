"""
京东金融金价 API 封装。
公开接口示例(无需鉴权):
    GET https://ms.jr.jd.com/gw/generic/hj/h5/m/latestPrice
真实返回结构(2026 年验证):
    {
      "resultCode": 0,
      "resultData": {
        "datas": {
          "productSku": "P005",
          "price": "974.87",
          "yesterdayPrice": "970.68",
          "upAndDownAmt": "+4.19",
          "upAndDownRate": "+0.43%",
          "demode": false,
          "id": 82274768,
          "time": "1780545279000"   # 毫秒时间戳
        },
        "status": "SUCCESS"
      },
      "success": true,
      ...
    }
该接口直接返回当前主推黄金现货(Au99.99 对应 SKU=P005),不支持多品类筛选。
本模块按"配置 product_code 仅作为显示标签"处理,实际写入数据库的 product_code
取 API 返回的 productSku,价格取 price(元/克)。
"""
import json
import logging
from datetime import datetime
from typing import Optional

import requests

import config
from db import standalone_conn

log = logging.getLogger("jd_gold")

# 浏览器 UA,避免被风控直接拒
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    ),
    "Referer": "https://m.jr.jd.com/",
    "Accept": "application/json,text/plain,*/*",
}


def _format_ts(ms_or_str) -> str:
    """京东 time 字段为 ms 时间戳字符串,这里转 'YYYY-MM-DD HH:MM:SS'。"""
    if ms_or_str is None or ms_or_str == "":
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        ms = int(ms_or_str)
        return datetime.fromtimestamp(ms / 1000).strftime("%Y-%m-%d %H:%M:%S")
    except (TypeError, ValueError):
        # 已经是字符串日期则原样返回
        return str(ms_or_str)


def fetch_jd_gold(product_code: Optional[str] = None, timeout: int = 8) -> dict:
    """
    调用京东金融返回标准化 dict;失败抛 RuntimeError。
    返回:
      { product_code, price(float), raw(dict), ts(str) }
    """
    label = product_code or config.GOLD_PRODUCT_CODE   # 显示用标签
    resp = requests.get(config.JD_GOLD_API, headers=_HEADERS, timeout=timeout)
    resp.raise_for_status()
    payload = resp.json()
    if str(payload.get("resultCode")) != "0":
        raise RuntimeError(f"京东返回非 0: {payload.get('resultMsg')}")
    data = (payload.get("resultData") or {}).get("datas") or {}
    if "price" not in data:
        raise RuntimeError(f"返回结构异常,缺少 price 字段: keys={list(data.keys())[:8]}")
    sku = data.get("productSku") or label
    return {
        "product_code": label or sku,    # 优先用用户配置的标签
        "sku": sku,                      # 实际 SKU(P005 等)
        "price": float(data["price"]),
        "raw": data,
        "ts": _format_ts(data.get("time")),
    }


def fetch_and_save(product_code: Optional[str] = None) -> dict:
    """
    拉取 + 写入 gold_price 表,返回最新插入信息。
    供监控进程定时调用 / 接口手动调用复用。
    """
    info = fetch_jd_gold(product_code)
    with standalone_conn() as c:
        cur = c.execute(
            """INSERT INTO gold_price(product_code, price, raw_json)
               VALUES (?,?,?)""",
            (info["product_code"], info["price"], json.dumps(info["raw"], ensure_ascii=False)),
        )
        info["id"] = cur.lastrowid
    log.info("[gold] 拉取成功 %s = %s", info["product_code"], info["price"])
    return {
        "id": info["id"],
        "product_code": info["product_code"],
        "price": info["price"],
        "ts": info["ts"],
    }
