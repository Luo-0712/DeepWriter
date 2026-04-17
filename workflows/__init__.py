"""DeepWriter 写作工作流模块

基于 LangGraph 的多智能体编排工作流。
"""

from workflows.graph import (
    compile_quick_workflow,
    compile_standard_workflow,
    create_quick_workflow,
    create_standard_workflow,
)
from workflows.models import (
    EditResult,
    EditSuggestion,
    Outline,
    ResearchNote,
    ResearchResult,
    ReviewFeedback,
    ReviewScores,
    Section,
    UserIntervention,
    WorkflowError,
)
from workflows.orchestrator import WritingOrchestrator
from workflows.state import WritingWorkflowState

__all__ = [
    # 工作流图
    "create_standard_workflow",
    "create_quick_workflow",
    "compile_standard_workflow",
    "compile_quick_workflow",
    # 编排器
    "WritingOrchestrator",
    # 状态
    "WritingWorkflowState",
    # 数据模型
    "Outline",
    "Section",
    "ResearchNote",
    "ResearchResult",
    "EditSuggestion",
    "EditResult",
    "ReviewFeedback",
    "ReviewScores",
    "UserIntervention",
    "WorkflowError",
]
