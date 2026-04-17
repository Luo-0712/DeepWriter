from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class TaskCreateRequest(BaseModel):
    session_id: str = Field(description="会话ID")
    task_type: str = Field(default="article", description="任务类型")
    topic: str = Field(..., min_length=1, description="主题")
    request: Optional[dict] = Field(default_factory=dict, description="请求详情")
    document_id: Optional[str] = Field(default=None, description="关联文档ID")


class TaskResponse(BaseModel):
    id: str = Field(description="任务ID")
    session_id: str = Field(description="会话ID")
    task_type: str = Field(description="任务类型")
    topic: str = Field(description="主题")
    status: str = Field(description="状态")
    progress: Optional[float] = Field(default=None, description="进度")
    result: Optional[str] = Field(default=None, description="结果")
    error_message: Optional[str] = Field(default=None, description="错误信息")
    created_at: datetime = Field(description="创建时间")
    updated_at: datetime = Field(description="更新时间")
    completed_at: Optional[datetime] = Field(default=None, description="完成时间")

    class Config:
        from_attributes = True


class TaskListResponse(BaseModel):
    total: int = Field(description="总数")
    items: list[TaskResponse] = Field(description="任务列表")


class TaskStatsResponse(BaseModel):
    pending: int = Field(description="待处理")
    running: int = Field(description="运行中")
    completed: int = Field(description="已完成")
    failed: int = Field(description="失败")
    total: int = Field(description="总数")
