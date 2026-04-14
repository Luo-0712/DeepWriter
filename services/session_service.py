"""
会话服务层

提供会话管理的高级业务逻辑。
"""

from typing import Optional

from db.database import Database, get_db
from db.models import Session as SessionModel
from db.repositories import (
    DocumentRepository,
    MessageRepository,
    SessionRepository,
    WritingTaskRepository,
)


class SessionService:
    """
    会话服务

    管理会话的生命周期和相关操作。
    """

    def __init__(self, db: Optional[Database] = None):
        self.db = db or get_db()
        self.session_repo = SessionRepository(self.db)
        self.message_repo = MessageRepository(self.db)
        self.document_repo = DocumentRepository(self.db)
        self.task_repo = WritingTaskRepository(self.db)

    def create_session(
        self, user_id: Optional[str] = None, title: str = "新会话", config: Optional[dict] = None
    ) -> SessionModel:
        """
        创建新会话

        Args:
            user_id: 用户 ID
            title: 会话标题
            config: 会话配置

        Returns:
            SessionModel: 创建的会话
        """
        session = SessionModel(
            user_id=user_id,
            title=title,
            config=config or {},
        )
        return self.session_repo.create(session)

    def get_session(self, session_id: str) -> Optional[SessionModel]:
        """
        获取会话

        Args:
            session_id: 会话 ID

        Returns:
            Optional[SessionModel]: 会话对象
        """
        return self.session_repo.get_by_id(session_id)

    def get_or_create_session(
        self, session_id: Optional[str] = None, user_id: Optional[str] = None
    ) -> SessionModel:
        """
        获取或创建会话

        Args:
            session_id: 会话 ID
            user_id: 用户 ID

        Returns:
            SessionModel: 会话对象
        """
        if session_id:
            session = self.session_repo.get_by_id(session_id)
            if session:
                return session
        return self.create_session(user_id=user_id)

    def list_user_sessions(self, user_id: str, limit: int = 100) -> list[SessionModel]:
        """
        获取用户的所有会话

        Args:
            user_id: 用户 ID
            limit: 限制数量

        Returns:
            list[SessionModel]: 会话列表
        """
        return self.session_repo.get_by_user_id(user_id, limit)

    def list_all_sessions(self, limit: int = 100, offset: int = 0) -> list[SessionModel]:
        """
        列出所有会话

        Args:
            limit: 限制数量
            offset: 偏移量

        Returns:
            list[SessionModel]: 会话列表
        """
        return self.session_repo.list_all(limit, offset)

    def update_session(self, session: SessionModel) -> SessionModel:
        """
        更新会话

        Args:
            session: 会话对象

        Returns:
            SessionModel: 更新后的会话
        """
        return self.session_repo.update(session)

    def update_session_title(self, session_id: str, title: str) -> bool:
        """
        更新会话标题

        Args:
            session_id: 会话 ID
            title: 新标题

        Returns:
            bool: 是否成功
        """
        return self.session_repo.update_title(session_id, title)

    def archive_session(self, session_id: str) -> bool:
        """
        归档会话

        Args:
            session_id: 会话 ID

        Returns:
            bool: 是否成功
        """
        session = self.session_repo.get_by_id(session_id)
        if session:
            session.status = "archived"
            self.session_repo.update(session)
            return True
        return False

    def delete_session(self, session_id: str) -> bool:
        """
        删除会话及其所有关联数据

        Args:
            session_id: 会话 ID

        Returns:
            bool: 是否成功
        """
        return self.session_repo.delete(session_id)

    def get_session_stats(self, session_id: str) -> dict:
        """
        获取会话统计信息

        Args:
            session_id: 会话 ID

        Returns:
            dict: 统计信息
        """
        message_count = self.message_repo.count_by_session_id(session_id)
        documents = self.document_repo.get_by_session_id(session_id)
        tasks = self.task_repo.get_by_session_id(session_id)

        return {
            "session_id": session_id,
            "message_count": message_count,
            "document_count": len(documents),
            "task_count": len(tasks),
            "documents": [{"id": d.id, "title": d.title, "status": d.status} for d in documents],
            "tasks": [{"id": t.id, "status": t.status, "topic": t.topic} for t in tasks],
        }


# 全局服务实例
_session_service: Optional[SessionService] = None


def get_session_service(db: Optional[Database] = None) -> SessionService:
    """获取全局 SessionService 实例"""
    global _session_service
    if _session_service is None:
        _session_service = SessionService(db)
    return _session_service
