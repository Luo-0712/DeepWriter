from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class DocumentCreateRequest(BaseModel):
    session_id: str = Field(description="会话ID")
    title: str = Field(..., min_length=1, description="文档标题")
    content: Optional[str] = Field(default="", description="文档内容")
    doc_type: Optional[str] = Field(default="article", description="文档类型")
    metadata: Optional[dict] = Field(default_factory=dict, description="元数据")


class DocumentUpdateRequest(BaseModel):
    title: Optional[str] = Field(default=None, description="文档标题")
    content: Optional[str] = Field(default=None, description="文档内容")
    create_version: bool = Field(default=False, description="是否创建版本")
    change_summary: Optional[str] = Field(default=None, description="变更摘要")


class DocumentResponse(BaseModel):
    id: str = Field(description="文档ID")
    session_id: str = Field(description="会话ID")
    title: str = Field(description="标题")
    content: str = Field(description="内容")
    doc_type: str = Field(description="类型")
    status: str = Field(description="状态")
    version_count: int = Field(default=0, description="版本数量")
    created_at: datetime = Field(description="创建时间")
    updated_at: datetime = Field(description="更新时间")

    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    total: int = Field(description="总数")
    items: list[DocumentResponse] = Field(description="文档列表")


class DocumentVersionResponse(BaseModel):
    id: int = Field(description="版本ID")
    document_id: str = Field(description="文档ID")
    version: int = Field(description="版本号")
    title: str = Field(description="标题")
    change_summary: Optional[str] = Field(description="变更摘要")
    created_at: datetime = Field(description="创建时间")

    class Config:
        from_attributes = True


class DocumentVersionListResponse(BaseModel):
    total: int = Field(description="总数")
    items: list[DocumentVersionResponse] = Field(description="版本列表")
