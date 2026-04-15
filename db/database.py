"""
数据库连接管理

支持 SQLite 和 PostgreSQL 数据库。
"""

import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Optional

from config.settings import DatabaseProvider, Settings, get_settings

_psycopg2 = None

def _get_psycopg2():
    global _psycopg2
    if _psycopg2 is None:
        import psycopg2
        from psycopg2 import pool
        from psycopg2.extras import RealDictCursor
        _psycopg2 = {"psycopg2": psycopg2, "pool": pool, "RealDictCursor": RealDictCursor}
    return _psycopg2


class Database:
    """
    数据库管理类

    支持 SQLite 和 PostgreSQL，提供数据库连接、初始化和事务管理功能。
    """

    _instance: Optional["Database"] = None
    _lock = threading.Lock()

    def __new__(cls, settings: Optional[Settings] = None) -> "Database":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self, settings: Optional[Settings] = None):
        if self._initialized:
            return

        self._settings = settings or get_settings()
        self._provider = self._settings.database_provider
        self._local = threading.local()

        if self._provider == DatabaseProvider.POSTGRESQL:
            self._init_postgresql()
        else:
            self._init_sqlite()

        self._initialized = True

    def _init_sqlite(self) -> None:
        """初始化SQLite连接"""
        import sqlite3

        db_path = self._settings.database_url or str(
            Path(__file__).parent.parent / "data" / "deepwriter.db"
        )
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.db_path = db_path

    def _init_postgresql(self) -> None:
        """初始化PostgreSQL连接池"""
        pg = _get_psycopg2()
        self._pg_pool = pg["pool"].ThreadedConnectionPool(
            minconn=1,
            maxconn=10,
            host=self._settings.postgresql_host,
            port=self._settings.postgresql_port,
            user=self._settings.postgresql_user,
            password=self._settings.postgresql_password,
            database=self._settings.postgresql_db,
        )

    def _get_sqlite_connection(self):
        """获取SQLite连接"""
        import sqlite3

        if not hasattr(self._local, "connection") or self._local.connection is None:
            self._local.connection = sqlite3.connect(
                self.db_path,
                check_same_thread=False,
                detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
            )
            self._local.connection.row_factory = sqlite3.Row
            self._local.connection.execute("PRAGMA foreign_keys = ON")
        return self._local.connection

    def _get_pg_connection(self):
        """获取PostgreSQL连接"""
        if not hasattr(self._local, "connection") or self._local.connection is None:
            self._local.connection = self._pg_pool.getconn()
            self._local.connection.autocommit = False
        return self._local.connection

    def _get_connection(self):
        """根据数据库类型获取连接"""
        if self._provider == DatabaseProvider.POSTGRESQL:
            return self._get_pg_connection()
        return self._get_sqlite_connection()

    def _return_pg_connection(self, conn) -> None:
        """归还PostgreSQL连接到池"""
        if self._provider == DatabaseProvider.POSTGRESQL and conn:
            self._pg_pool.putconn(conn)

    @contextmanager
    def session(self):
        """
        数据库会话上下文管理器
        """
        conn = self._get_connection()
        try:
            yield conn
            if self._provider == DatabaseProvider.POSTGRESQL:
                conn.commit()
            else:
                conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            if self._provider == DatabaseProvider.POSTGRESQL:
                self._return_pg_connection(conn)
                self._local.connection = None

    @contextmanager
    def cursor(self):
        """
        数据库游标上下文管理器
        """
        with self.session() as conn:
            if self._provider == DatabaseProvider.POSTGRESQL:
                pg = _get_psycopg2()
                cursor = conn.cursor(cursor_factory=pg["RealDictCursor"])
            else:
                cursor = conn.cursor()
            try:
                yield cursor
            finally:
                cursor.close()

    def execute(self, sql: str, parameters: tuple = ()):
        """
        执行 SQL 语句
        """
        with self.cursor() as cursor:
            cursor.execute(sql, parameters)
            return cursor

    def executemany(self, sql: str, parameters: list[tuple]):
        """
        批量执行 SQL 语句
        """
        with self.cursor() as cursor:
            cursor.executemany(sql, parameters)
            return cursor

    def fetchone(self, sql: str, parameters: tuple = ()):
        """
        查询单条记录
        """
        with self.cursor() as cursor:
            cursor.execute(sql, parameters)
            return cursor.fetchone()

    def fetchall(self, sql: str, parameters: tuple = ()):
        """
        查询所有记录
        """
        with self.cursor() as cursor:
            cursor.execute(sql, parameters)
            return cursor.fetchall()

    def init_tables(self) -> None:
        """初始化数据库表结构"""
        if self._provider == DatabaseProvider.POSTGRESQL:
            self._init_postgresql_tables()
        else:
            self._init_sqlite_tables()

    def _init_sqlite_tables(self) -> None:
        """初始化SQLite表结构"""
        import sqlite3

        schema = """
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            title TEXT DEFAULT '新会话',
            config_json TEXT DEFAULT '{}',
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
            content TEXT NOT NULL,
            metadata_json TEXT DEFAULT '{}',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
        );

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

        CREATE INDEX IF NOT EXISTS idx_messages_session_id ON messages(session_id);
        CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at);
        CREATE INDEX IF NOT EXISTS idx_documents_session_id ON documents(session_id);
        CREATE INDEX IF NOT EXISTS idx_document_versions_document_id ON document_versions(document_id);
        CREATE INDEX IF NOT EXISTS idx_writing_tasks_session_id ON writing_tasks(session_id);
        CREATE INDEX IF NOT EXISTS idx_writing_tasks_status ON writing_tasks(status);
        """

        with self.session() as conn:
            conn.executescript(schema)

    def _init_postgresql_tables(self) -> None:
        """初始化PostgreSQL表结构"""
        schema = """
        CREATE TABLE IF NOT EXISTS sessions (
            id VARCHAR(36) PRIMARY KEY,
            user_id VARCHAR(255),
            title VARCHAR(500) DEFAULT '新会话',
            config_json TEXT DEFAULT '{}',
            status VARCHAR(50) DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS messages (
            id SERIAL PRIMARY KEY,
            session_id VARCHAR(36) NOT NULL,
            role VARCHAR(50) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
            content TEXT NOT NULL,
            metadata_json TEXT DEFAULT '{}',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS documents (
            id VARCHAR(36) PRIMARY KEY,
            session_id VARCHAR(36) NOT NULL,
            title VARCHAR(500) NOT NULL,
            content TEXT DEFAULT '',
            doc_type VARCHAR(50) DEFAULT 'article',
            status VARCHAR(50) DEFAULT 'draft',
            metadata_json TEXT DEFAULT '{}',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS document_versions (
            id SERIAL PRIMARY KEY,
            document_id VARCHAR(36) NOT NULL,
            version INTEGER NOT NULL,
            title VARCHAR(500) NOT NULL,
            content TEXT NOT NULL,
            change_summary TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
            UNIQUE(document_id, version)
        );

        CREATE TABLE IF NOT EXISTS writing_tasks (
            id VARCHAR(36) PRIMARY KEY,
            session_id VARCHAR(36) NOT NULL,
            document_id VARCHAR(36),
            task_type VARCHAR(50) NOT NULL,
            topic VARCHAR(1000) NOT NULL,
            request_json TEXT DEFAULT '{}',
            state_json TEXT DEFAULT '{}',
            status VARCHAR(50) DEFAULT 'pending',
            result TEXT,
            error_message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE,
            FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE SET NULL
        );

        CREATE INDEX IF NOT EXISTS idx_messages_session_id ON messages(session_id);
        CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at);
        CREATE INDEX IF NOT EXISTS idx_documents_session_id ON documents(session_id);
        CREATE INDEX IF NOT EXISTS idx_document_versions_document_id ON document_versions(document_id);
        CREATE INDEX IF NOT EXISTS idx_writing_tasks_session_id ON writing_tasks(session_id);
        CREATE INDEX IF NOT EXISTS idx_writing_tasks_status ON writing_tasks(status);
        """

        with self.session() as conn:
            with conn.cursor() as cursor:
                cursor.execute(schema)

    def close(self) -> None:
        """关闭数据库连接"""
        if self._provider == DatabaseProvider.POSTGRESQL:
            if hasattr(self, "_pg_pool") and self._pg_pool:
                self._pg_pool.closeall()
        else:
            if hasattr(self._local, "connection") and self._local.connection:
                self._local.connection.close()
                self._local.connection = None

    def drop_all_tables(self) -> None:
        """删除所有表（危险操作，仅用于测试）"""
        if self._provider == DatabaseProvider.POSTGRESQL:
            with self.session() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT table_name FROM information_schema.tables
                        WHERE table_schema = 'public'
                    """)
                    tables = cursor.fetchall()
                    for table in tables:
                        cursor.execute(f"DROP TABLE IF EXISTS {table[0]} CASCADE")
        else:
            import sqlite3

            with self.session() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
                )
                tables = cursor.fetchall()
                for table in tables:
                    cursor.execute(f"DROP TABLE IF EXISTS {table[0]}")


def get_db(settings: Optional[Settings] = None) -> Database:
    """
    获取数据库实例

    Args:
        settings: 配置对象

    Returns:
        Database: 数据库实例
    """
    db = Database(settings)
    return db
