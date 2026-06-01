"""
京东金融金价 API 封装。
公开接口示例(无需鉴权):
    GET https://ms.jr.jd.com/gw/generic/hj/h5/m/latestPrice
返回结构(简化):
    {
      "resultCode": 0,
      "resultData": {
        "datas": {
          "Au99.99": {
            "productSku": "Au99.99",
            "price": "612.55",
            "demode": "0.55",
            "yesterdayPrice": "612.00",
            "time": "2026-06-01 10:30:00",
            ...
          },
          "Au100g": { ... },
          ...
        }
      }
    }
本模块只关心 config.GOLD_PRODUCT_CODE 这一只品类。
"""
import json
import logging
from datetime import datetime

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


def fetch_jd_gold(product_code: str | None = None, timeout: int = 8) -> dict:
    """
    调用京东金融返回原始 dict;失败抛 RuntimeError。
    """
    code = product_code or config.GOLD_PRODUCT_CODE
    resp = requests.get(config.JD_GOLD_API, headers=_HEADERS, timeout=timeout)
    resp.raise_for_status()
    payload = resp.json()
    if str(payload.get("resultCode")) != "0":
        raise RuntimeError(f"京东返回非 0: {payload.get('resultMsg')}")
    datas = (payload.get("resultData") or {}).get("datas") or {}
    one = datas.get(code)
    if not one or "price" not in one:
        raise RuntimeError(f"未在返回中找到 {code},现有: {list(datas.keys())[:5]}")
    return {
        "product_code": code,
        "price": float(one["price"]),
        "raw": one,
        "ts": one.get("time") or datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


def fetch_and_save(product_code: str | None = None) -> dict:
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
