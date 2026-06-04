"""
金价定时监控独立进程(监听 9000 端口仅暴露 /health)。
- 启动时读取 gold_config 决定是否启用、拉取间隔
- 每分钟回读一次配置,如间隔变更则重新调度,实现热更新
- 调用 services.jd_gold.fetch_and_save 写入历史
- 异常不会让进程崩溃,记录日志后下一次继续
"""
import logging
import sys
import time
from typing import Tuple

from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, jsonify

import config
from db import init_schema, standalone_conn
from services.jd_gold import fetch_and_save

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
log = logging.getLogger("monitor")

# 全局调度器,只跑一个名为 gold_job 的任务
scheduler = BackgroundScheduler(timezone="Asia/Shanghai")


def _read_config() -> Tuple[int, str, bool]:
    """从 SQLite 读取最新配置(interval_sec, product_code, enabled)。"""
    with standalone_conn() as c:
        row = c.execute("SELECT * FROM gold_config WHERE id=1").fetchone()
    if row is None:
        return config.GOLD_POLL_INTERVAL, config.GOLD_PRODUCT_CODE, True
    return int(row["poll_interval_sec"]), row["product_code"], bool(row["enabled"])


def _do_fetch():
    """调度器调用的实际拉取动作,捕获所有异常。"""
    try:
        interval, code, enabled = _read_config()
        if not enabled:
            log.info("[gold] 监控已禁用,跳过拉取")
            return
        fetch_and_save(code)
    except Exception as e:    # noqa: BLE001
        log.exception("[gold] 拉取失败: %s", e)


def _ensure_schedule():
    """根据配置确保 gold_job 存在且 interval 与配置一致。"""
    interval, code, enabled = _read_config()
    job = scheduler.get_job("gold_job")
    desired = interval if enabled else None

    if not enabled:
        if job:
            scheduler.remove_job("gold_job")
            log.info("[gold] 已根据配置移除任务")
        return

    if job is None:
        scheduler.add_job(
            _do_fetch,
            "interval",
            seconds=interval,
            id="gold_job",
            next_run_time=None,    # 立刻跑一次? 用下面的 do_now 触发
            max_instances=1,
            coalesce=True,
        )
        log.info("[gold] 已添加任务,间隔 %ss, 品类 %s", interval, code)
        # 启动即触发一次,无需等到第一个周期
        scheduler.add_job(_do_fetch, id="gold_job_initial", max_instances=1)
    else:
        # 检查 interval 是否需要变更
        current = job.trigger.interval.total_seconds() if hasattr(job.trigger, "interval") else None
        if current != interval:
            scheduler.reschedule_job("gold_job", trigger="interval", seconds=interval)
            log.info("[gold] 间隔已更新为 %ss", interval)


def _config_watcher():
    """每 60 秒回读配置,实现监控间隔/启停的热更新。"""
    while True:
        try:
            _ensure_schedule()
        except Exception as e:    # noqa: BLE001
            log.exception("[watcher] %s", e)
        time.sleep(60)


# Flask 仅用于健康检查,9000 端口
app = Flask(__name__)


@app.get("/health")
def health():
    job = scheduler.get_job("gold_job")
    return jsonify(
        status="ok",
        job_running=job is not None,
        next_run=str(job.next_run_time) if job and job.next_run_time else None,
    )


def main():
    init_schema()
    scheduler.start()
    _ensure_schedule()

    # 后台线程做热更新
    import threading
    t = threading.Thread(target=_config_watcher, daemon=True)
    t.start()

    log.info("金价监控启动,健康检查端口 %s", config.MONITOR_PORT)
    app.run(host="0.0.0.0", port=config.MONITOR_PORT, debug=False, use_reloader=False)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        scheduler.shutdown(wait=False)
        sys.exit(0)
