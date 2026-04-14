"""
Session 基础类

定义 Session 和 SessionStore 的抽象接口。
"""

import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field

from services.models import DocumentVersion, SessionConfig, WritingState


class Session(BaseModel):
    """
    Session 模型

    保存完整的会话状态，包括写作状态、配置和历史版本。
    """

    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    config: SessionConfig = Field(default_factory=SessionConfig)
    writing_state: Optional[WritingState] = None
    versions: list[DocumentVersion] = Field(default_factory=list)
    message_history: list[dict[str, Any]] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    def add_message(self, role: str, content: str) -> None:
        """添加消息到历史记录"""
        self.message_history.append({"role": role, "content": content, "timestamp": datetime.now().isoformat()})
        self.updated_at = datetime.now()

    def add_version(self, version: DocumentVersion) -> None:
        """添加文档版本"""
        self.versions.append(version)
        self.updated_at = datetime.now()

    def get_latest_version(self) -> Optional[DocumentVersion]:
        """获取最新版本"""
        if not self.versions:
            return None
        return max(self.versions, key=lambda v: v.version)

    def get_current_content(self) -> str:
        """获取当前内容"""
        if self.writing_state and self.writing_state.final_text:
            return self.writing_state.final_text
        latest = self.get_latest_version()
        return latest.content if latest else ""

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Session":
        """从字典创建"""
        return cls(**data)


class SessionStore(ABC):
    """
    Session 存储抽象接口

    支持不同的存储后端实现（内存、文件、数据库）。
    """

    @abstractmethod
    def save(self, session: Session) -> None:
        """保存 Session"""
        pass

    @abstractmethod
    def load(self, session_id: str) -> Optional[Session]:
        """加载 Session"""
        pass

    @abstractmethod
    def delete(self, session_id: str) -> None:
        """删除 Session"""
        pass

    @abstractmethod
    def list_sessions(self) -> list[str]:
        """列出所有 Session ID"""
        pass

    @abstractmethod
    def clear(self) -> None:
        """清空所有 Session"""
        pass
