from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class MessageCreateRequest(BaseModel):
    role: str = Field(default="user", description="角色 (user/assistant/system)")
    content: str = Field(..., min_length=1, description="消息内容")
    metadata: Optional[dict] = Field(default_factory=dict, description="元数据")


class MessageResponse(BaseModel):
    id: int = Field(description="消息ID")
    session_id: str = Field(description="会话ID")
    role: str = Field(description="角色")
    content: str = Field(description="内容")
    metadata: dict = Field(description="元数据")
    created_at: datetime = Field(description="创建时间")

    class Config:
        from_attributes = True


class MessageListResponse(BaseModel):
    total: int = Field(description="总数")
    items: list[MessageResponse] = Field(description="消息列表")


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="用户消息")
    stream: bool = Field(default=False, description="是否流式响应")


class ChatResponse(BaseModel):
    message: str = Field(description="回复内容")
    session_id: str = Field(description="会话ID")
