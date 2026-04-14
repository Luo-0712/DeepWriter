"""
数据模型层

定义数据库实体模型，对应 SQLite 表结构。
"""

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional


def generate_uuid() -> str:
    """生成 UUID 字符串"""
    return str(uuid.uuid4())


def json_dumps(data: dict) -> str:
    """将字典转为 JSON 字符串"""
    return json.dumps(data, ensure_ascii=False, default=str)


def json_loads(data: str) -> dict:
    """将 JSON 字符串转为字典"""
    return json.loads(data) if data else {}


def parse_datetime(value: Any) -> datetime:
    """解析日期时间，处理多种格式"""
    if value is None:
        return datetime.now()
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        # 处理带 Z 的 ISO 格式
        value = value.replace('Z', '+00:00')
        # 处理没有时信息的格式
        if ' ' in value and 'T' not in value:
            value = value.replace(' ', 'T')
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            # 尝试其他格式
            for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M:%S.%f']:
                try:
                    return datetime.strptime(value.split('.')[0] if '.' in value else value, fmt)
                except ValueError:
                    continue
    return datetime.now()


@dataclass
class Session:
    """
    会话实体

    对应数据库 sessions 表。
    """

    id: str = field(default_factory=generate_uuid)
    user_id: Optional[str] = None
    title: str = "新会话"
    config: dict = field(default_factory=dict)
    status: str = "active"  # active, archived, deleted
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    @classmethod
    def from_row(cls, row: Any) -> "Session":
        """从数据库行创建实例"""
        return cls(
            id=row["id"],
            user_id=row["user_id"],
            title=row["title"],
            config=json_loads(row["config_json"]),
            status=row["status"],
            created_at=parse_datetime(row["created_at"]),
            updated_at=parse_datetime(row["updated_at"]),
        )

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "config": self.config,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass
class Message:
    """
    消息实体

    对应数据库 messages 表。
    """

    id: Optional[int] = None
    session_id: str = ""
    role: str = "user"  # user, assistant, system
    content: str = ""
    metadata: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

    @classmethod
    def from_row(cls, row: Any) -> "Message":
        """从数据库行创建实例"""
        return cls(
            id=row["id"],
            session_id=row["session_id"],
            role=row["role"],
            content=row["content"],
            metadata=json_loads(row["metadata_json"]),
            created_at=parse_datetime(row["created_at"]),
        )

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "session_id": self.session_id,
            "role": self.role,
            "content": self.content,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
        }

    def to_chat_dict(self) -> dict[str, str]:
        """转换为聊天格式字典"""
        return {
            "role": self.role,
            "content": self.content,
        }


@dataclass
class Document:
    """
    文档实体

    对应数据库 documents 表。
    """

    id: str = field(default_factory=generate_uuid)
    session_id: str = ""
    title: str = ""
    content: str = ""
    doc_type: str = "article"  # article, blog, report, etc.
    status: str = "draft"  # draft, published, archived
    metadata: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    @classmethod
    def from_row(cls, row: Any) -> "Document":
        """从数据库行创建实例"""
        return cls(
            id=row["id"],
            session_id=row["session_id"],
            title=row["title"],
            content=row["content"],
            doc_type=row["doc_type"],
            status=row["status"],
            metadata=json_loads(row["metadata_json"]),
            created_at=parse_datetime(row["created_at"]),
            updated_at=parse_datetime(row["updated_at"]),
        )

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "session_id": self.session_id,
            "title": self.title,
            "content": self.content,
            "doc_type": self.doc_type,
            "status": self.status,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass
class DocumentVersion:
    """
    文档版本实体

    对应数据库 document_versions 表。
    """

    id: Optional[int] = None
    document_id: str = ""
    version: int = 1
    title: str = ""
    content: str = ""
    change_summary: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)

    @classmethod
    def from_row(cls, row: Any) -> "DocumentVersion":
        """从数据库行创建实例"""
        return cls(
            id=row["id"],
            document_id=row["document_id"],
            version=row["version"],
            title=row["title"],
            content=row["content"],
            change_summary=row["change_summary"],
            created_at=parse_datetime(row["created_at"]),
        )

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "document_id": self.document_id,
            "version": self.version,
            "title": self.title,
            "content": self.content,
            "change_summary": self.change_summary,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class WritingTask:
    """
    写作任务实体

    对应数据库 writing_tasks 表。
    """

    id: str = field(default_factory=generate_uuid)
    session_id: str = ""
    document_id: Optional[str] = None
    task_type: str = "article"  # article, blog, report, etc.
    topic: str = ""
    request: dict = field(default_factory=dict)
    state: dict = field(default_factory=dict)
    status: str = "pending"  # pending, running, completed, failed
    result: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None

    @classmethod
    def from_row(cls, row: Any) -> "WritingTask":
        """从数据库行创建实例"""
        completed_at = row["completed_at"]
        if completed_at:
            completed_at = parse_datetime(completed_at)

        return cls(
            id=row["id"],
            session_id=row["session_id"],
            document_id=row["document_id"],
            task_type=row["task_type"],
            topic=row["topic"],
            request=json_loads(row["request_json"]),
            state=json_loads(row["state_json"]),
            status=row["status"],
            result=row["result"],
            error_message=row["error_message"],
            created_at=parse_datetime(row["created_at"]),
            updated_at=parse_datetime(row["updated_at"]),
            completed_at=completed_at,
        )

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "session_id": self.session_id,
            "document_id": self.document_id,
            "task_type": self.task_type,
            "topic": self.topic,
            "request": self.request,
            "state": self.state,
            "status": self.status,
            "result": self.result,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }
