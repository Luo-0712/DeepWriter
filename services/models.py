"""
DeepWriter 统一数据模型

定义核心数据结构，用于写作请求、状态管理和文档版本控制。
"""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class WritingRequest(BaseModel):
    """
    写作请求模型

    用于封装用户写作需求的所有参数。
    """

    task_type: str = Field(
        default="article",
        description="任务类型：article, blog, report, proposal, email, copy, social_media",
    )
    topic: str = Field(..., description="文章主题")
    audience: Optional[str] = Field(None, description="目标读者")
    goal: Optional[str] = Field(None, description="写作目的")
    tone: Optional[str] = Field(None, description="语气风格")
    length: Optional[str] = Field(None, description="期望长度：short, medium, long")
    language: str = Field(default="zh", description="语言：zh, en")
    use_rag: bool = Field(default=False, description="是否使用 RAG 检索")
    use_web: bool = Field(default=False, description="是否使用网络搜索")
    session_id: Optional[str] = Field(None, description="会话 ID")
    style: str = Field(default="professional", description="写作风格")
    extra_context: Optional[str] = Field(None, description="额外上下文信息")
    metadata: dict[str, Any] = Field(default_factory=dict, description="元数据")

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WritingRequest":
        """从字典创建"""
        return cls(**data)


class WritingState(BaseModel):
    """
    写作状态模型

    用于跟踪写作任务的完整状态和中间产物。
    """

    request: WritingRequest = Field(..., description="原始写作请求")
    outline: list[str] = Field(default_factory=list, description="文章大纲")
    research_notes: list[dict[str, Any]] = Field(
        default_factory=list, description="研究笔记"
    )
    draft_sections: list[str] = Field(default_factory=list, description="草稿章节")
    review_feedback: list[str] = Field(default_factory=list, description="评审反馈")
    final_text: str = Field(default="", description="最终文本")
    current_stage: str = Field(default="init", description="当前阶段")
    metadata: dict[str, Any] = Field(default_factory=dict, description="元数据")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")

    def add_outline(self, outline: list[str]) -> None:
        """添加大纲"""
        self.outline = outline
        self.updated_at = datetime.now()

    def add_research_note(self, note: dict[str, Any]) -> None:
        """添加研究笔记"""
        self.research_notes.append(note)
        self.updated_at = datetime.now()

    def add_draft_section(self, section: str) -> None:
        """添加草稿章节"""
        self.draft_sections.append(section)
        self.updated_at = datetime.now()

    def add_review_feedback(self, feedback: str) -> None:
        """添加评审反馈"""
        self.review_feedback.append(feedback)
        self.updated_at = datetime.now()

    def set_final_text(self, text: str) -> None:
        """设置最终文本"""
        self.final_text = text
        self.updated_at = datetime.now()

    def set_stage(self, stage: str) -> None:
        """设置当前阶段"""
        self.current_stage = stage
        self.updated_at = datetime.now()

    def get_full_draft(self) -> str:
        """获取完整草稿"""
        return "\n\n".join(self.draft_sections)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WritingState":
        """从字典创建"""
        if "request" in data and isinstance(data["request"], dict):
            data["request"] = WritingRequest.from_dict(data["request"])
        return cls(**data)


class DocumentVersion(BaseModel):
    """
    文档版本模型

    用于记录文档的历史版本和变更摘要。
    """

    document_id: str = Field(..., description="文档 ID")
    version: int = Field(..., description="版本号")
    title: str = Field(..., description="标题")
    content: str = Field(..., description="内容")
    change_summary: Optional[str] = Field(None, description="变更摘要")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    metadata: dict[str, Any] = Field(default_factory=dict, description="元数据")

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DocumentVersion":
        """从字典创建"""
        return cls(**data)


class SessionConfig(BaseModel):
    """
    会话配置模型

    用于保存用户的会话级配置。
    """

    session_id: str = Field(..., description="会话 ID")
    user_id: Optional[str] = Field(None, description="用户 ID")
    style: str = Field(default="professional", description="默认写作风格")
    language: str = Field(default="zh", description="默认语言")
    tone: Optional[str] = Field(None, description="默认语气")
    use_rag: bool = Field(default=False, description="是否启用 RAG")
    use_web: bool = Field(default=False, description="是否启用网络搜索")
    metadata: dict[str, Any] = Field(default_factory=dict, description="元数据")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SessionConfig":
        """从字典创建"""
        return cls(**data)


# 任务类型常量
TASK_TYPES = {
    "article": "文章",
    "blog": "博客",
    "report": "报告",
    "proposal": "方案",
    "email": "邮件",
    "copy": "营销文案",
    "social_media": "社交媒体",
    "academic": "学术论文",
    "story": "故事",
    "script": "脚本",
}

# 长度选项
LENGTH_OPTIONS = {
    "short": "短 (300-500 字)",
    "medium": "中 (500-1500 字)",
    "long": "长 (1500+ 字)",
}

# 写作风格
WRITING_STYLES = [
    "professional",  # 专业
    "casual",  # 休闲
    "academic",  # 学术
    "creative",  # 创意
    "formal",  # 正式
    "friendly",  # 友好
    "persuasive",  # 说服性
    "informative",  # 信息性
]
