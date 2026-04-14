"""
数据库初始化脚本

用于创建数据库表结构和初始数据。
"""

import argparse
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from db.database import get_db


def init_database(db_path: str | None = None, drop_all: bool = False) -> None:
    """
    初始化数据库

    Args:
        db_path: 数据库文件路径
        drop_all: 是否先删除所有表
    """
    db = get_db(db_path)

    if drop_all:
        print("正在删除所有表...")
        db.drop_all_tables()
        print("所有表已删除")

    print("正在创建表结构...")
    db.init_tables()
    print(f"数据库初始化完成: {db.db_path}")


def main():
    parser = argparse.ArgumentParser(description="DeepWriter 数据库初始化工具")
    parser.add_argument(
        "--db-path",
        type=str,
        default=None,
        help="数据库文件路径 (默认: ./data/deepwriter.db)",
    )
    parser.add_argument(
        "--drop-all",
        action="store_true",
        help="删除所有表后重新创建 (危险操作！)",
    )

    args = parser.parse_args()

    if args.drop_all:
        confirm = input("确定要删除所有表吗？此操作不可恢复！(yes/no): ")
        if confirm.lower() != "yes":
            print("操作已取消")
            return

    init_database(args.db_path, args.drop_all)


if __name__ == "__main__":
    main()
