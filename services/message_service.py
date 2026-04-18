"""
消息服务层

提供消息管理的高级业务逻辑。
"""

from typing import Optional

from db.database import Database, get_db
from db.models import Message as MessageModel
from db.repositories import MessageRepository, SessionRepository


class MessageService:
    """
    消息服务

    管理消息的创建、查询和历史记录。
    """

    def __init__(self, db: Optional[Database] = None):
        self.db = db or get_db()
        self.message_repo = MessageRepository(self.db)
        self.session_repo = SessionRepository(self.db)

    def create_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[dict] = None,
    ) -> MessageModel:
        """
        创建消息

        Args:
            session_id: 会话 ID
            role: 角色 (user/assistant/system)
            content: 消息内容
            metadata: 元数据

        Returns:
            MessageModel: 创建的消息
        """
        message = MessageModel(
            session_id=session_id,
            role=role,
            content=content,
            metadata=metadata or {},
        )
        message = self.message_repo.create(message)

        # 更新会话的 updated_at
        session = self.session_repo.get_by_id(session_id)
        if session:
            self.session_repo.update(session)

        return message

    def add_user_message(self, session_id: str, content: str, metadata: Optional[dict] = None) -> MessageModel:
        """添加用户消息"""
        return self.create_message(session_id, "user", content, metadata)

    async def generate_title_for_first_message(self, session_id: str, first_message: str) -> bool:
        """为会话的第一条消息生成标题

        Args:
            session_id: 会话 ID
            first_message: 第一条用户消息

        Returns:
            bool: 是否成功生成标题
        """
        try:
            from agents.specialized.summarizer_agent import SummarizerAgent

            summarizer = SummarizerAgent()
            response = await summarizer.execute(first_message)

            if response.success and response.content:
                return self.session_repo.update_title(session_id, response.content)
            return False
        except Exception:
            return False

    def add_assistant_message(self, session_id: str, content: str, metadata: Optional[dict] = None) -> MessageModel:
        """添加助手消息"""
        return self.create_message(session_id, "assistant", content, metadata)

    def add_system_message(self, session_id: str, content: str, metadata: Optional[dict] = None) -> MessageModel:
        """添加系统消息"""
        return self.create_message(session_id, "system", content, metadata)

    def get_message(self, message_id: int) -> Optional[MessageModel]:
        """
        获取消息

        Args:
            message_id: 消息 ID

        Returns:
            Optional[MessageModel]: 消息对象
        """
        return self.message_repo.get_by_id(message_id)

    def get_session_messages(
        self, session_id: str, limit: int = 100, offset: int = 0
    ) -> list[MessageModel]:
        """
        获取会话的所有消息

        Args:
            session_id: 会话 ID
            limit: 限制数量
            offset: 偏移量

        Returns:
            list[MessageModel]: 消息列表
        """
        return self.message_repo.get_by_session_id(session_id, limit, offset)

    def get_recent_messages(self, session_id: str, limit: int = 10) -> list[MessageModel]:
        """
        获取最近的对话历史

        Args:
            session_id: 会话 ID
            limit: 限制数量

        Returns:
            list[MessageModel]: 消息列表
        """
        return self.message_repo.get_recent_by_session_id(session_id, limit)

    def get_chat_history(self, session_id: str, limit: int = 10) -> list[dict[str, str]]:
        """
        获取聊天历史（用于 LLM 上下文）

        Args:
            session_id: 会话 ID
            limit: 限制数量

        Returns:
            list[dict[str, str]]: 聊天历史列表
        """
        messages = self.get_recent_messages(session_id, limit)
        return [msg.to_chat_dict() for msg in messages]

    def clear_session_messages(self, session_id: str) -> int:
        """
        清空会话的所有消息

        Args:
            session_id: 会话 ID

        Returns:
            int: 删除的消息数量
        """
        return self.message_repo.delete_by_session_id(session_id)

    def delete_message(self, message_id: int) -> bool:
        """
        删除消息

        Args:
            message_id: 消息 ID

        Returns:
            bool: 是否成功
        """
        return self.message_repo.delete(message_id)

    def count_messages(self, session_id: str) -> int:
        """
        统计会话消息数量

        Args:
            session_id: 会话 ID

        Returns:
            int: 消息数量
        """
        return self.message_repo.count_by_session_id(session_id)


# 全局服务实例
_message_service: Optional[MessageService] = None


def get_message_service(db: Optional[Database] = None) -> MessageService:
    """获取全局 MessageService 实例"""
    global _message_service
    if _message_service is None:
        _message_service = MessageService(db)
    return _message_service
