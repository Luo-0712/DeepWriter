"""
DeepWriter 数据库模块

提供 SQLite 数据库连接、模型定义和数据访问层。
"""

from db.database import Database, get_db
from db.models import Session, Message, Document, DocumentVersion, WritingTask
from db.repositories import (
    SessionRepository,
    MessageRepository,
    DocumentRepository,
    DocumentVersionRepository,
    WritingTaskRepository,
)

__all__ = [
    "Database",
    "get_db",
    "Session",
    "Message",
    "Document",
    "DocumentVersion",
    "WritingTask",
    "SessionRepository",
    "MessageRepository",
    "DocumentRepository",
    "DocumentVersionRepository",
    "WritingTaskRepository",
]
