"""工作流图定义

使用 LangGraph StateGraph 定义标准和快速两种写作工作流。
"""

import logging

from langgraph.graph import END, StateGraph

from workflows.conditions import route_after_critic, route_after_planning
from workflows.nodes import (
    critic_node,
    editor_node,
    planner_node,
    researcher_node,
    writer_node,
)
from workflows.state import WritingWorkflowState

logger = logging.getLogger(__name__)


def create_standard_workflow() -> StateGraph:
    """创建标准写作工作流

    流程：规划 → (研究) → 起草 → 编辑 → 评审 → (循环修改或结束)

    研究环节通过条件路由控制，根据 use_rag/use_web 配置决定是否执行。
    评审后根据评分决定是否需要循环修改。
    """
    workflow = StateGraph(WritingWorkflowState)

    # 添加节点
    workflow.add_node("plan", planner_node)
    workflow.add_node("research", researcher_node)
    workflow.add_node("write", writer_node)
    workflow.add_node("edit", editor_node)
    workflow.add_node("critic", critic_node)

    # 设置入口
    workflow.set_entry_point("plan")

    # 规划后条件路由：研究或直接起草
    workflow.add_conditional_edges(
        "plan",
        route_after_planning,
        {
            "research": "research",
            "write": "write",
            "end": END,
        },
    )

    # 研究 → 起草
    workflow.add_edge("research", "write")

    # 起草 → 编辑
    workflow.add_edge("write", "edit")

    # 编辑 → 评审
    workflow.add_edge("edit", "critic")

    # 评审后条件路由：修改或结束
    workflow.add_conditional_edges(
        "critic",
        route_after_critic,
        {
            "revise": "write",
            "end": END,
        },
    )

    return workflow


def create_quick_workflow() -> StateGraph:
    """创建快速写作工作流

    流程：规划 → 起草 → 编辑 → 评审（无研究环节、无循环修改）

    适用于不需要深度研究的快速写作场景。
    """
    workflow = StateGraph(WritingWorkflowState)

    # 添加节点
    workflow.add_node("plan", planner_node)
    workflow.add_node("write", writer_node)
    workflow.add_node("edit", editor_node)
    workflow.add_node("critic", critic_node)

    # 设置入口和线性流程
    workflow.set_entry_point("plan")
    workflow.add_edge("plan", "write")
    workflow.add_edge("write", "edit")
    workflow.add_edge("edit", "critic")
    workflow.add_edge("critic", END)

    return workflow


def compile_standard_workflow(checkpointer=None):
    """编译标准工作流为可执行图"""
    workflow = create_standard_workflow()
    # TODO [CHECKPOINT]: 集成 checkpointer 实现检查点持久化
    return workflow.compile(checkpointer=checkpointer)


def compile_quick_workflow(checkpointer=None):
    """编译快速工作流为可执行图"""
    workflow = create_quick_workflow()
    return workflow.compile(checkpointer=checkpointer)
