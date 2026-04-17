"""条件路由函数

定义工作流中的条件边路由逻辑。
"""

import logging

from workflows.state import WritingWorkflowState

logger = logging.getLogger(__name__)


def route_after_planning(state: WritingWorkflowState) -> str:
    """规划后路由：决定是否需要研究环节

    根据 use_rag 和 use_web 配置决定下一步：
    - 如果启用了 RAG 或网络搜索，进入研究节点
    - 否则跳过研究，直接进入起草节点
    """
    if state.get("error"):
        logger.warning(f"规划阶段有错误，直接结束: {state['error']}")
        return "end"

    use_rag = state.get("use_rag", False)
    use_web = state.get("use_web", False)

    if use_rag or use_web:
        logger.info("路由到研究节点（RAG/Web 已启用）")
        return "research"
    else:
        logger.info("跳过研究节点，直接进入起草")
        return "write"


def route_after_critic(state: WritingWorkflowState) -> str:
    """评审后路由：根据评审结果决定下一步

    - 如果评审通过或达到最大迭代次数，结束工作流
    - 如果需要修改，返回编辑节点重新修改
    """
    if state.get("error"):
        logger.warning(f"评审阶段有错误: {state['error']}")
        return "end"

    should_continue = state.get("should_continue", False)

    if should_continue:
        logger.info("评审未通过，返回起草节点修改")
        return "revise"
    else:
        logger.info("评审通过或达到最大迭代次数，结束工作流")
        return "end"
