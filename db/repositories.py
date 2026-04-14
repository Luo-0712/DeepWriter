"""
数据访问层 (Repository)

提供实体的 CRUD 操作，封装数据库访问逻辑。
"""

from typing import Any, Optional

from db.database import Database
from db.models import Document, DocumentVersion, Message, Session, WritingTask, json_dumps


class BaseRepository:
    """基础仓库类"""

    def __init__(self, db: Database):
        self.db = db


class SessionRepository(BaseRepository):
    """会话数据访问"""

    def create(self, session: Session) -> Session:
        """创建会话"""
        sql = """
            INSERT INTO sessions (id, user_id, title, config_json, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        self.db.execute(
            sql,
            (
                session.id,
                session.user_id,
                session.title,
                json_dumps(session.config),
                session.status,
                session.created_at,
                session.updated_at,
            ),
        )
        return session

    def get_by_id(self, session_id: str) -> Optional[Session]:
        """根据 ID 获取会话"""
        sql = "SELECT * FROM sessions WHERE id = ?"
        row = self.db.fetchone(sql, (session_id,))
        return Session.from_row(row) if row else None

    def get_by_user_id(self, user_id: str, limit: int = 100) -> list[Session]:
        """获取用户的所有会话"""
        sql = "SELECT * FROM sessions WHERE user_id = ? ORDER BY updated_at DESC LIMIT ?"
        rows = self.db.fetchall(sql, (user_id, limit))
        return [Session.from_row(row) for row in rows]

    def list_all(self, limit: int = 100, offset: int = 0) -> list[Session]:
        """列出所有会话"""
        sql = "SELECT * FROM sessions ORDER BY updated_at DESC LIMIT ? OFFSET ?"
        rows = self.db.fetchall(sql, (limit, offset))
        return [Session.from_row(row) for row in rows]

    def update(self, session: Session) -> Session:
        """更新会话"""
        sql = """
            UPDATE sessions
            SET title = ?, config_json = ?, status = ?, updated_at = ?
            WHERE id = ?
        """
        session.updated_at = __import__("datetime").datetime.now()
        self.db.execute(
            sql,
            (
                session.title,
                json_dumps(session.config),
                session.status,
                session.updated_at,
                session.id,
            ),
        )
        return session

    def delete(self, session_id: str) -> bool:
        """删除会话"""
        sql = "DELETE FROM sessions WHERE id = ?"
        cursor = self.db.execute(sql, (session_id,))
        return cursor.rowcount > 0

    def update_title(self, session_id: str, title: str) -> bool:
        """更新会话标题"""
        sql = "UPDATE sessions SET title = ?, updated_at = ? WHERE id = ?"
        cursor = self.db.execute(sql, (title, __import__("datetime").datetime.now(), session_id))
        return cursor.rowcount > 0


class MessageRepository(BaseRepository):
    """消息数据访问"""

    def create(self, message: Message) -> Message:
        """创建消息"""
        sql = """
            INSERT INTO messages (session_id, role, content, metadata_json, created_at)
            VALUES (?, ?, ?, ?, ?)
        """
        cursor = self.db.execute(
            sql,
            (
                message.session_id,
                message.role,
                message.content,
                json_dumps(message.metadata),
                message.created_at,
            ),
        )
        message.id = cursor.lastrowid
        return message

    def get_by_id(self, message_id: int) -> Optional[Message]:
        """根据 ID 获取消息"""
        sql = "SELECT * FROM messages WHERE id = ?"
        row = self.db.fetchone(sql, (message_id,))
        return Message.from_row(row) if row else None

    def get_by_session_id(
        self, session_id: str, limit: int = 100, offset: int = 0
    ) -> list[Message]:
        """获取会话的所有消息"""
        sql = """
            SELECT * FROM messages
            WHERE session_id = ?
            ORDER BY created_at ASC
            LIMIT ? OFFSET ?
        """
        rows = self.db.fetchall(sql, (session_id, limit, offset))
        return [Message.from_row(row) for row in rows]

    def get_recent_by_session_id(self, session_id: str, limit: int = 10) -> list[Message]:
        """获取会话的最近消息"""
        sql = """
            SELECT * FROM messages
            WHERE session_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        """
        rows = self.db.fetchall(sql, (session_id, limit))
        return [Message.from_row(row) for row in reversed(rows)]

    def delete_by_session_id(self, session_id: str) -> int:
        """删除会话的所有消息"""
        sql = "DELETE FROM messages WHERE session_id = ?"
        cursor = self.db.execute(sql, (session_id,))
        return cursor.rowcount

    def delete(self, message_id: int) -> bool:
        """删除消息"""
        sql = "DELETE FROM messages WHERE id = ?"
        cursor = self.db.execute(sql, (message_id,))
        return cursor.rowcount > 0

    def count_by_session_id(self, session_id: str) -> int:
        """统计会话消息数量"""
        sql = "SELECT COUNT(*) as count FROM messages WHERE session_id = ?"
        row = self.db.fetchone(sql, (session_id,))
        return row["count"] if row else 0


class DocumentRepository(BaseRepository):
    """文档数据访问"""

    def create(self, document: Document) -> Document:
        """创建文档"""
        sql = """
            INSERT INTO documents (id, session_id, title, content, doc_type, status, metadata_json, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        self.db.execute(
            sql,
            (
                document.id,
                document.session_id,
                document.title,
                document.content,
                document.doc_type,
                document.status,
                json_dumps(document.metadata),
                document.created_at,
                document.updated_at,
            ),
        )
        return document

    def get_by_id(self, document_id: str) -> Optional[Document]:
        """根据 ID 获取文档"""
        sql = "SELECT * FROM documents WHERE id = ?"
        row = self.db.fetchone(sql, (document_id,))
        return Document.from_row(row) if row else None

    def get_by_session_id(self, session_id: str) -> list[Document]:
        """获取会话的所有文档"""
        sql = "SELECT * FROM documents WHERE session_id = ? ORDER BY updated_at DESC"
        rows = self.db.fetchall(sql, (session_id,))
        return [Document.from_row(row) for row in rows]

    def list_all(self, limit: int = 100, offset: int = 0) -> list[Document]:
        """列出所有文档"""
        sql = "SELECT * FROM documents ORDER BY updated_at DESC LIMIT ? OFFSET ?"
        rows = self.db.fetchall(sql, (limit, offset))
        return [Document.from_row(row) for row in rows]

    def update(self, document: Document) -> Document:
        """更新文档"""
        sql = """
            UPDATE documents
            SET title = ?, content = ?, doc_type = ?, status = ?, metadata_json = ?, updated_at = ?
            WHERE id = ?
        """
        document.updated_at = __import__("datetime").datetime.now()
        self.db.execute(
            sql,
            (
                document.title,
                document.content,
                document.doc_type,
                document.status,
                json_dumps(document.metadata),
                document.updated_at,
                document.id,
            ),
        )
        return document

    def update_content(self, document_id: str, content: str) -> bool:
        """更新文档内容"""
        sql = "UPDATE documents SET content = ?, updated_at = ? WHERE id = ?"
        cursor = self.db.execute(sql, (content, __import__("datetime").datetime.now(), document_id))
        return cursor.rowcount > 0

    def update_status(self, document_id: str, status: str) -> bool:
        """更新文档状态"""
        sql = "UPDATE documents SET status = ?, updated_at = ? WHERE id = ?"
        cursor = self.db.execute(sql, (status, __import__("datetime").datetime.now(), document_id))
        return cursor.rowcount > 0

    def delete(self, document_id: str) -> bool:
        """删除文档"""
        sql = "DELETE FROM documents WHERE id = ?"
        cursor = self.db.execute(sql, (document_id,))
        return cursor.rowcount > 0

    def delete_by_session_id(self, session_id: str) -> int:
        """删除会话的所有文档"""
        sql = "DELETE FROM documents WHERE session_id = ?"
        cursor = self.db.execute(sql, (session_id,))
        return cursor.rowcount


class DocumentVersionRepository(BaseRepository):
    """文档版本数据访问"""

    def create(self, version: DocumentVersion) -> DocumentVersion:
        """创建文档版本"""
        sql = """
            INSERT INTO document_versions (document_id, version, title, content, change_summary, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        cursor = self.db.execute(
            sql,
            (
                version.document_id,
                version.version,
                version.title,
                version.content,
                version.change_summary,
                version.created_at,
            ),
        )
        version.id = cursor.lastrowid
        return version

    def get_by_id(self, version_id: int) -> Optional[DocumentVersion]:
        """根据 ID 获取版本"""
        sql = "SELECT * FROM document_versions WHERE id = ?"
        row = self.db.fetchone(sql, (version_id,))
        return DocumentVersion.from_row(row) if row else None

    def get_by_document_id(self, document_id: str) -> list[DocumentVersion]:
        """获取文档的所有版本"""
        sql = "SELECT * FROM document_versions WHERE document_id = ? ORDER BY version ASC"
        rows = self.db.fetchall(sql, (document_id,))
        return [DocumentVersion.from_row(row) for row in rows]

    def get_latest_by_document_id(self, document_id: str) -> Optional[DocumentVersion]:
        """获取文档的最新版本"""
        sql = "SELECT * FROM document_versions WHERE document_id = ? ORDER BY version DESC LIMIT 1"
        row = self.db.fetchone(sql, (document_id,))
        return DocumentVersion.from_row(row) if row else None

    def get_next_version_number(self, document_id: str) -> int:
        """获取下一个版本号"""
        sql = "SELECT MAX(version) as max_version FROM document_versions WHERE document_id = ?"
        row = self.db.fetchone(sql, (document_id,))
        return (row["max_version"] or 0) + 1

    def delete_by_document_id(self, document_id: str) -> int:
        """删除文档的所有版本"""
        sql = "DELETE FROM document_versions WHERE document_id = ?"
        cursor = self.db.execute(sql, (document_id,))
        return cursor.rowcount

    def delete(self, version_id: int) -> bool:
        """删除版本"""
        sql = "DELETE FROM document_versions WHERE id = ?"
        cursor = self.db.execute(sql, (version_id,))
        return cursor.rowcount > 0


class WritingTaskRepository(BaseRepository):
    """写作任务数据访问"""

    def create(self, task: WritingTask) -> WritingTask:
        """创建写作任务"""
        sql = """
            INSERT INTO writing_tasks (id, session_id, document_id, task_type, topic, request_json, state_json, status, result, error_message, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        self.db.execute(
            sql,
            (
                task.id,
                task.session_id,
                task.document_id,
                task.task_type,
                task.topic,
                json_dumps(task.request),
                json_dumps(task.state),
                task.status,
                task.result,
                task.error_message,
                task.created_at,
                task.updated_at,
            ),
        )
        return task

    def get_by_id(self, task_id: str) -> Optional[WritingTask]:
        """根据 ID 获取任务"""
        sql = "SELECT * FROM writing_tasks WHERE id = ?"
        row = self.db.fetchone(sql, (task_id,))
        return WritingTask.from_row(row) if row else None

    def get_by_session_id(self, session_id: str) -> list[WritingTask]:
        """获取会话的所有任务"""
        sql = "SELECT * FROM writing_tasks WHERE session_id = ? ORDER BY created_at DESC"
        rows = self.db.fetchall(sql, (session_id,))
        return [WritingTask.from_row(row) for row in rows]

    def get_by_document_id(self, document_id: str) -> list[WritingTask]:
        """获取文档的所有任务"""
        sql = "SELECT * FROM writing_tasks WHERE document_id = ? ORDER BY created_at DESC"
        rows = self.db.fetchall(sql, (document_id,))
        return [WritingTask.from_row(row) for row in rows]

    def list_by_status(self, status: str, limit: int = 100) -> list[WritingTask]:
        """根据状态列出任务"""
        sql = "SELECT * FROM writing_tasks WHERE status = ? ORDER BY created_at DESC LIMIT ?"
        rows = self.db.fetchall(sql, (status, limit))
        return [WritingTask.from_row(row) for row in rows]

    def list_all(self, limit: int = 100, offset: int = 0) -> list[WritingTask]:
        """列出所有任务"""
        sql = "SELECT * FROM writing_tasks ORDER BY created_at DESC LIMIT ? OFFSET ?"
        rows = self.db.fetchall(sql, (limit, offset))
        return [WritingTask.from_row(row) for row in rows]

    def update(self, task: WritingTask) -> WritingTask:
        """更新任务"""
        sql = """
            UPDATE writing_tasks
            SET status = ?, state_json = ?, result = ?, error_message = ?, updated_at = ?
            WHERE id = ?
        """
        task.updated_at = __import__("datetime").datetime.now()
        self.db.execute(
            sql,
            (
                task.status,
                json_dumps(task.state),
                task.result,
                task.error_message,
                task.updated_at,
                task.id,
            ),
        )
        return task

    def update_status(self, task_id: str, status: str) -> bool:
        """更新任务状态"""
        sql = "UPDATE writing_tasks SET status = ?, updated_at = ? WHERE id = ?"
        cursor = self.db.execute(sql, (status, __import__("datetime").datetime.now(), task_id))
        return cursor.rowcount > 0

    def complete_task(self, task_id: str, result: str) -> bool:
        """完成任务"""
        sql = """
            UPDATE writing_tasks
            SET status = 'completed', result = ?, completed_at = ?, updated_at = ?
            WHERE id = ?
        """
        now = __import__("datetime").datetime.now()
        cursor = self.db.execute(sql, (result, now, now, task_id))
        return cursor.rowcount > 0

    def fail_task(self, task_id: str, error_message: str) -> bool:
        """标记任务失败"""
        sql = """
            UPDATE writing_tasks
            SET status = 'failed', error_message = ?, completed_at = ?, updated_at = ?
            WHERE id = ?
        """
        now = __import__("datetime").datetime.now()
        cursor = self.db.execute(sql, (error_message, now, now, task_id))
        return cursor.rowcount > 0

    def delete(self, task_id: str) -> bool:
        """删除任务"""
        sql = "DELETE FROM writing_tasks WHERE id = ?"
        cursor = self.db.execute(sql, (task_id,))
        return cursor.rowcount > 0

    def delete_by_session_id(self, session_id: str) -> int:
        """删除会话的所有任务"""
        sql = "DELETE FROM writing_tasks WHERE session_id = ?"
        cursor = self.db.execute(sql, (session_id,))
        return cursor.rowcount
