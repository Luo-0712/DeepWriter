"""LangGraph 工作流状态定义

使用 TypedDict 定义工作流状态，供 LangGraph StateGraph 使用。
"""

from typing import Annotated, Any, Optional, TypedDict

from langgraph.graph.message import add_messages


class WritingWorkflowState(TypedDict):
    """写作工作流状态

    LangGraph 使用 TypedDict 作为状态定义，每个字段代表工作流中的一个状态切片。
    """
    # 输入
    user_input: str
    topic: str
    audience: str
    goal: str
    tone: str
    length: str
    style: str
    language: str
    use_rag: bool
    use_web: bool

    # 中间产物
    outline: dict[str, Any]
    research_notes: dict[str, Any]
    draft_content: str
    edit_result: dict[str, Any]
    review_feedback: dict[str, Any]

    # 控制流
    current_stage: str
    iteration_count: int
    max_iterations: int
    should_continue: bool
    error: str

    # 最终输出
    final_content: str
