"""
数据库连接管理

提供 SQLite 数据库连接池和会话管理。
"""

import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Optional


class Database:
    """
    SQLite 数据库管理类

    提供数据库连接、初始化和事务管理功能。
    """

    _instance: Optional["Database"] = None
    _lock = threading.Lock()

    def __new__(cls, db_path: Optional[str] = None) -> "Database":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self, db_path: Optional[str] = None):
        if self._initialized:
            return

        self.db_path = db_path or str(Path(__file__).parent.parent / "data" / "deepwriter.db")
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._local = threading.local()
        self._initialized = True

    def _get_connection(self) -> sqlite3.Connection:
        """获取线程本地连接"""
        if not hasattr(self._local, "connection") or self._local.connection is None:
            self._local.connection = sqlite3.connect(
                self.db_path,
                check_same_thread=False,
                detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
            )
            self._local.connection.row_factory = sqlite3.Row
            self._local.connection.execute("PRAGMA foreign_keys = ON")
        return self._local.connection

    @contextmanager
    def session(self):
        """
        数据库会话上下文管理器

        Yields:
            sqlite3.Connection: 数据库连接
        """
        conn = self._get_connection()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise

    @contextmanager
    def cursor(self):
        """
        数据库游标上下文管理器

        Yields:
            sqlite3.Cursor: 数据库游标
        """
        with self.session() as conn:
            cursor = conn.cursor()
            try:
                yield cursor
            finally:
                cursor.close()

    def execute(self, sql: str, parameters: tuple = ()) -> sqlite3.Cursor:
        """
        执行 SQL 语句

        Args:
            sql: SQL 语句
            parameters: 参数

        Returns:
            sqlite3.Cursor: 游标
        """
        with self.cursor() as cursor:
            cursor.execute(sql, parameters)
            return cursor

    def executemany(self, sql: str, parameters: list[tuple]) -> sqlite3.Cursor:
        """
        批量执行 SQL 语句

        Args:
            sql: SQL 语句
            parameters: 参数列表

        Returns:
            sqlite3.Cursor: 游标
        """
        with self.cursor() as cursor:
            cursor.executemany(sql, parameters)
            return cursor

    def fetchone(self, sql: str, parameters: tuple = ()) -> Optional[sqlite3.Row]:
        """
        查询单条记录

        Args:
            sql: SQL 语句
            parameters: 参数

        Returns:
            Optional[sqlite3.Row]: 查询结果
        """
        with self.cursor() as cursor:
            cursor.execute(sql, parameters)
            return cursor.fetchone()

    def fetchall(self, sql: str, parameters: tuple = ()) -> list[sqlite3.Row]:
        """
        查询所有记录

        Args:
            sql: SQL 语句
            parameters: 参数

        Returns:
            list[sqlite3.Row]: 查询结果列表
        """
        with self.cursor() as cursor:
            cursor.execute(sql, parameters)
            return cursor.fetchall()

    def init_tables(self) -> None:
        """初始化数据库表结构"""
        schema = """
        -- 会话表
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            title TEXT DEFAULT '新会话',
            config_json TEXT DEFAULT '{}',
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- 消息表
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
            content TEXT NOT NULL,
            metadata_json TEXT DEFAULT '{}',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
        );

        -- 文档表
        CREATE TABLE IF NOT EXISTS documents (
            id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            title TEXT NOT NULL,
            content TEXT DEFAULT '',
            doc_type TEXT DEFAULT 'article',
            status TEXT DEFAULT 'draft',
            metadata_json TEXT DEFAULT '{}',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
        );

        -- 文档版本表
        CREATE TABLE IF NOT EXISTS document_versions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id TEXT NOT NULL,
            version INTEGER NOT NULL,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            change_summary TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
            UNIQUE(document_id, version)
        );

        -- 写作任务表
        CREATE TABLE IF NOT EXISTS writing_tasks (
            id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            document_id TEXT,
            task_type TEXT NOT NULL,
            topic TEXT NOT NULL,
            request_json TEXT DEFAULT '{}',
            state_json TEXT DEFAULT '{}',
            status TEXT DEFAULT 'pending',
            result TEXT,
            error_message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE,
            FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE SET NULL
        );

        -- 创建索引
        CREATE INDEX IF NOT EXISTS idx_messages_session_id ON messages(session_id);
        CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at);
        CREATE INDEX IF NOT EXISTS idx_documents_session_id ON documents(session_id);
        CREATE INDEX IF NOT EXISTS idx_document_versions_document_id ON document_versions(document_id);
        CREATE INDEX IF NOT EXISTS idx_writing_tasks_session_id ON writing_tasks(session_id);
        CREATE INDEX IF NOT EXISTS idx_writing_tasks_status ON writing_tasks(status);
        """

        with self.session() as conn:
            conn.executescript(schema)

    def close(self) -> None:
        """关闭数据库连接"""
        if hasattr(self._local, "connection") and self._local.connection:
            self._local.connection.close()
            self._local.connection = None

    def drop_all_tables(self) -> None:
        """删除所有表（危险操作，仅用于测试）"""
        with self.session() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
            tables = cursor.fetchall()
            for table in tables:
                cursor.execute(f"DROP TABLE IF EXISTS {table[0]}")


def get_db(db_path: Optional[str] = None) -> Database:
    """
    获取数据库实例

    Args:
        db_path: 数据库文件路径

    Returns:
        Database: 数据库实例
    """
    db = Database(db_path)
    return db
