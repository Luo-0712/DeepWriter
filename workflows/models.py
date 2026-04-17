"""工作流数据模型

定义工作流中各阶段使用的数据结构。
"""

from typing import Any, Optional

from pydantic import BaseModel, Field


class Section(BaseModel):
    """章节定义"""
    title: str = Field(..., description="章节标题")
    key_points: list[str] = Field(default_factory=list, description="关键要点")
    estimated_words: int = Field(default=300, description="预计字数")


class Outline(BaseModel):
    """大纲结构"""
    title: str = Field(default="", description="文章标题")
    summary: str = Field(default="", description="文章摘要")
    sections: list[Section] = Field(default_factory=list, description="章节列表")
    total_estimated_words: int = Field(default=0, description="总预计字数")
    keywords: list[str] = Field(default_factory=list, description="关键词")


class ResearchNote(BaseModel):
    """研究笔记"""
    section_title: str = Field(default="", description="对应章节标题")
    findings: list[str] = Field(default_factory=list, description="研究发现")
    key_facts: list[str] = Field(default_factory=list, description="关键事实")
    references: list[str] = Field(default_factory=list, description="参考来源")
    suggestions: str = Field(default="", description="写作建议")


class ResearchResult(BaseModel):
    """研究结果"""
    notes: list[ResearchNote] = Field(default_factory=list, description="研究笔记列表")
    overall_insights: str = Field(default="", description="整体研究洞察")
    gaps: list[str] = Field(default_factory=list, description="信息空缺")


class EditSuggestion(BaseModel):
    """编辑建议"""
    type: str = Field(default="", description="建议类型")
    location: str = Field(default="", description="位置描述")
    issue: str = Field(default="", description="问题描述")
    fix: str = Field(default="", description="修改建议")


class EditResult(BaseModel):
    """编辑结果"""
    suggestions: list[EditSuggestion] = Field(default_factory=list, description="建议列表")
    revised_content: str = Field(default="", description="修改后的内容")
    summary: str = Field(default="", description="编辑总结")


class ReviewScores(BaseModel):
    """评审评分"""
    content_quality: float = Field(default=0.0, description="内容质量")
    structure: float = Field(default=0.0, description="结构组织")
    language: float = Field(default=0.0, description="语言表达")
    readability: float = Field(default=0.0, description="可读性")
    goal_achievement: float = Field(default=0.0, description="目标达成")


class ReviewFeedback(BaseModel):
    """评审反馈"""
    scores: ReviewScores = Field(default_factory=ReviewScores, description="评分")
    overall_score: float = Field(default=0.0, description="总分")
    passed: bool = Field(default=False, description="是否通过")
    strengths: list[str] = Field(default_factory=list, description="优点")
    weaknesses: list[str] = Field(default_factory=list, description="不足")
    suggestions: list[str] = Field(default_factory=list, description="改进建议")
    verdict: str = Field(default="", description="评审结论")


class UserIntervention(BaseModel):
    """用户干预（占位符，延后实现）"""
    # TODO [HUMAN_REVIEW]: 实现用户干预数据结构
    action: str = Field(default="", description="干预类型")
    content: str = Field(default="", description="干预内容")
    target_stage: str = Field(default="", description="目标阶段")


class WorkflowError(Exception):
    """工作流异常"""
    def __init__(self, message: str, stage: str = "", details: Optional[dict] = None):
        self.stage = stage
        self.details = details or {}
        super().__init__(message)
