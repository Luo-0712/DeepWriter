from typing import Optional, List
from pydantic import BaseModel, Field


class Section(BaseModel):
    id: str = Field(description="章节ID")
    title: str = Field(description="标题")
    description: str = Field(description="描述")
    estimated_words: int = Field(description="预计字数")


class WritingRequest(BaseModel):
    session_id: str = Field(description="会话ID")
    task_type: str = Field(default="article", description="任务类型")
    topic: str = Field(..., min_length=1, description="主题")
    audience: Optional[str] = Field(default=None, description="目标读者")
    goal: Optional[str] = Field(default=None, description="写作目的")
    tone: Optional[str] = Field(default=None, description="语气")
    length: Optional[str] = Field(default="medium", description="长度")
    language: str = Field(default="zh", description="语言")
    style: str = Field(default="professional", description="风格")
    use_rag: bool = Field(default=False, description="是否使用RAG")
    use_web: bool = Field(default=False, description="是否使用网络搜索")
    extra_context: Optional[str] = Field(default=None, description="额外上下文")


class OutlineResponse(BaseModel):
    title: str = Field(description="标题")
    sections: List[Section] = Field(description="章节列表")
    estimated_length: str = Field(description="预计长度")


class DraftResponse(BaseModel):
    content: str = Field(description="内容")
    word_count: int = Field(description="字数")


class EditRequest(BaseModel):
    content: str = Field(..., min_length=1, description="内容")
    edit_type: str = Field(..., description="编辑类型")
    instructions: str = Field(..., description="编辑要求")


class EditResponse(BaseModel):
    content: str = Field(description="编辑后内容")
    changes: Optional[List[str]] = Field(default=None, description="修改说明")


class WritingProgressResponse(BaseModel):
    task_id: str = Field(description="任务ID")
    stage: str = Field(description="当前阶段")
    progress: float = Field(description="进度")
    message: str = Field(description="消息")
    partial_result: Optional[str] = Field(default=None, description="部分结果")
