"""
SQLite 连接与表初始化。
- 每次请求获取一个连接(Flask g 缓存),避免线程安全问题
- 启动时执行 init_schema() 确保所有表存在
- 启动时若 admin 表为空,使用 config.ADMIN_USERNAME / ADMIN_PASSWORD 初始化一条管理员记录
"""
import sqlite3
from contextlib import contextmanager
from werkzeug.security import generate_password_hash
from flask import g

import config


def get_conn() -> sqlite3.Connection:
    """获取请求级别的数据库连接,Flask 会在请求结束时关闭。"""
    conn = getattr(g, "_db_conn", None)
    if conn is None:
        conn = sqlite3.connect(config.DB_PATH)
        conn.row_factory = sqlite3.Row  # 返回类字典对象
        conn.execute("PRAGMA foreign_keys = ON")
        g._db_conn = conn
    return conn


def close_conn(_exc=None):
    """Flask teardown 钩子调用,关闭连接。"""
    conn = g.pop("_db_conn", None)
    if conn is not None:
        conn.close()


@contextmanager
def standalone_conn():
    """
    脚本/独立进程使用的连接管理器(不依赖 Flask g)。
    用法: with standalone_conn() as c: c.execute(...)
    """
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


SCHEMA_SQL = """
-- 管理员表(单条记录)
CREATE TABLE IF NOT EXISTS admin (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 知识文档
CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    category TEXT DEFAULT '默认',
    content TEXT DEFAULT '',          -- Markdown 原文
    summary TEXT DEFAULT '',          -- 列表摘要(从 content 截取)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_docs_cat ON documents(category);
CREATE INDEX IF NOT EXISTS idx_docs_updated ON documents(updated_at DESC);

-- 金价拉取配置(单行,id 强制为 1)
CREATE TABLE IF NOT EXISTS gold_config (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    product_code TEXT DEFAULT 'Au99.99',
    poll_interval_sec INTEGER DEFAULT 300,
    enabled INTEGER DEFAULT 1,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 金价历史
CREATE TABLE IF NOT EXISTS gold_price (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_code TEXT NOT NULL,
    price REAL NOT NULL,            -- 元/克
    raw_json TEXT,                  -- 原始返回保留,便于排查
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_gp_time ON gold_price(fetched_at DESC);
CREATE INDEX IF NOT EXISTS idx_gp_code_time ON gold_price(product_code, fetched_at DESC);
"""


def init_schema():
    """创建表 + 写入默认管理员/默认金价配置(幂等)。"""
    with standalone_conn() as c:
        c.executescript(SCHEMA_SQL)

        # 默认管理员
        row = c.execute("SELECT COUNT(*) AS n FROM admin").fetchone()
        if row["n"] == 0:
            c.execute(
                "INSERT INTO admin(username, password_hash) VALUES (?, ?)",
                (
                    config.ADMIN_USERNAME,
                    generate_password_hash(config.ADMIN_PASSWORD),
                ),
            )

        # 默认金价配置
        row = c.execute("SELECT COUNT(*) AS n FROM gold_config").fetchone()
        if row["n"] == 0:
            c.execute(
                """INSERT INTO gold_config(id, product_code, poll_interval_sec, enabled)
                   VALUES (1, ?, ?, 1)""",
                (config.GOLD_PRODUCT_CODE, config.GOLD_POLL_INTERVAL),
            )
