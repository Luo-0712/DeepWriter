from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class SessionCreateRequest(BaseModel):
    title: Optional[str] = Field(default="新会话", description="会话标题")
    config: Optional[dict] = Field(default_factory=dict, description="会话配置")


class SessionUpdateRequest(BaseModel):
    title: Optional[str] = Field(default=None, description="会话标题")
    config: Optional[dict] = Field(default=None, description="会话配置")


class SessionResponse(BaseModel):
    id: str = Field(description="会话ID")
    title: str = Field(description="会话标题")
    status: str = Field(description="会话状态")
    message_count: int = Field(default=0, description="消息数量")
    document_count: int = Field(default=0, description="文档数量")
    created_at: datetime = Field(description="创建时间")
    updated_at: datetime = Field(description="更新时间")

    class Config:
        from_attributes = True


class SessionListResponse(BaseModel):
    total: int = Field(description="总数")
    items: list[SessionResponse] = Field(description="会话列表")


class SessionStatsResponse(BaseModel):
    session_id: str = Field(description="会话ID")
    message_count: int = Field(description="消息数量")
    document_count: int = Field(description="文档数量")
    task_count: int = Field(description="任务数量")
    documents: list[dict] = Field(description="文档列表")
    tasks: list[dict] = Field(description="任务列表")
