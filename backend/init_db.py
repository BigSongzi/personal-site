"""
独立运行的数据库初始化脚本:
    python init_db.py
等价于在主服务启动时自动调用 db.init_schema(),
此脚本主要用于部署阶段提前建库或迁移环境时手动执行。
"""
from db import init_schema

if __name__ == "__main__":
    init_schema()
    print("数据库初始化完成。")
