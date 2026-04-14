"""
Session 管理器

提供统一的 Session 管理接口，支持创建、加载、保存和切换 Session。
"""

from typing import Optional

from services.models import SessionConfig, WritingRequest, WritingState
from services.session.base import Session, SessionStore
from services.session.file_store import FileSessionStore


class SessionManager:
    """
    Session 管理器

    管理 Session 的生命周期，包括创建、加载、保存和切换。
    """

    def __init__(self, store: Optional[SessionStore] = None):
        """
        初始化 Session 管理器

        Args:
            store: Session 存储实现，默认为 FileSessionStore
        """
        self.store = store or FileSessionStore()
        self._current_session: Optional[Session] = None

    @property
    def current_session(self) -> Optional[Session]:
        """获取当前 Session"""
        return self._current_session

    @property
    def current_session_id(self) -> Optional[str]:
        """获取当前 Session ID"""
        return self._current_session.session_id if self._current_session else None

    def create_session(
        self,
        config: Optional[SessionConfig] = None,
        save: bool = True,
    ) -> Session:
        """
        创建新 Session

        Args:
            config: Session 配置，默认创建
            save: 是否立即保存

        Returns:
            新创建的 Session
        """
        session = Session(config=config or SessionConfig(session_id=""))
        # 更新 session_id 为生成的 UUID
        if config is None or not config.session_id:
            session.config.session_id = session.session_id
        self._current_session = session
        if save:
            self.save_session()
        return session

    def load_session(self, session_id: str) -> Optional[Session]:
        """
        加载 Session

        Args:
            session_id: Session ID

        Returns:
            加载的 Session，不存在则返回 None
        """
        session = self.store.load(session_id)
        if session:
            self._current_session = session
        return session

    def save_session(self) -> None:
        """保存当前 Session"""
        if self._current_session:
            self.store.save(self._current_session)

    def delete_session(self, session_id: Optional[str] = None) -> None:
        """
        删除 Session

        Args:
            session_id: Session ID，默认删除当前 Session
        """
        session_id = session_id or self.current_session_id
        if session_id:
            self.store.delete(session_id)
            if self._current_session and self._current_session.session_id == session_id:
                self._current_session = None

    def switch_session(self, session_id: str) -> bool:
        """
        切换 Session

        Args:
            session_id: 目标 Session ID

        Returns:
            是否成功切换
        """
        session = self.load_session(session_id)
        return session is not None

    def list_sessions(self) -> list[str]:
        """列出所有 Session ID"""
        return self.store.list_sessions()

    def start_writing(self, request: WritingRequest) -> WritingState:
        """
        开始新的写作任务

        Args:
            request: 写作请求

        Returns:
            创建的 WritingState
        """
        if not self._current_session:
            self.create_session()

        state = WritingState(request=request)
        self._current_session.writing_state = state
        self.save_session()
        return state

    def add_message(self, role: str, content: str) -> None:
        """
        添加消息到当前 Session

        Args:
            role: 角色 (user/assistant/system)
            content: 消息内容
        """
        if self._current_session:
            self._current_session.add_message(role, content)
            self.save_session()

    def get_message_history(self, limit: int = 10) -> list[dict]:
        """
        获取消息历史

        Args:
            limit: 返回最近的消息数量

        Returns:
            消息历史列表
        """
        if not self._current_session:
            return []
        return self._current_session.message_history[-limit:]

    def clear_current(self) -> None:
        """清空当前 Session 引用"""
        self._current_session = None

    def get_or_create_session(self, session_id: Optional[str] = None) -> Session:
        """
        获取或创建 Session

        Args:
            session_id: Session ID，如果为 None 或不存在则创建新 Session

        Returns:
            Session 对象
        """
        if session_id:
            session = self.load_session(session_id)
            if session:
                return session
        return self.create_session()


# 全局实例
_session_manager: Optional[SessionManager] = None


def get_session_manager() -> SessionManager:
    """获取全局 SessionManager 实例"""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager
