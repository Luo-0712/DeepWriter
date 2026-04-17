from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class KnowledgeBaseCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, description="知识库名称")
    description: Optional[str] = Field(default=None, description="描述")


class KnowledgeBaseResponse(BaseModel):
    name: str = Field(description="名称")
    description: Optional[str] = Field(description="描述")
    document_count: int = Field(description="文档数量")
    created_at: Optional[datetime] = Field(default=None, description="创建时间")


class KnowledgeBaseListResponse(BaseModel):
    total: int = Field(description="总数")
    items: List[KnowledgeBaseResponse] = Field(description="知识库列表")


class DocumentUploadResponse(BaseModel):
    uploaded_count: int = Field(description="上传成功数量")
    failed_files: List[str] = Field(description="失败的文件")


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, description="查询")
    top_k: int = Field(default=5, ge=1, le=20, description="返回数量")


class SearchResult(BaseModel):
    content: str = Field(description="内容")
    source: str = Field(description="来源")
    relevance_score: float = Field(description="相关度分数")
    metadata: dict = Field(description="元数据")


class SearchResponse(BaseModel):
    query: str = Field(description="查询")
    total: int = Field(description="结果数量")
    results: List[SearchResult] = Field(description="结果列表")
