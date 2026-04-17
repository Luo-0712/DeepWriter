"""规划节点 - 调用 PlannerAgent 生成大纲"""

import logging

from workflows.state import WritingWorkflowState

logger = logging.getLogger(__name__)


async def planner_node(state: WritingWorkflowState) -> dict:
    """规划节点：根据用户输入生成文章大纲"""
    logger.info("进入规划节点")

    try:
        from agents.specialized.planner_agent import PlannerAgent

        agent = PlannerAgent(language=state.get("language", "zh"))

        response = await agent.execute(
            input_text=state["user_input"],
            topic=state.get("topic", state["user_input"]),
            audience=state.get("audience", "通用读者"),
            goal=state.get("goal", "信息传达"),
            tone=state.get("tone", "专业"),
            length=state.get("length", "medium"),
        )

        if not response.success:
            return {
                "error": f"规划失败: {response.error}",
                "current_stage": "planning_failed",
            }

        outline = response.metadata.get("outline", {"raw_content": response.content})

        logger.info(f"大纲生成完成: {outline.get('title', 'untitled')}")
        return {
            "outline": outline,
            "current_stage": "planned",
            "error": "",
        }

    except Exception as e:
        logger.error(f"规划节点异常: {e}")
        return {
            "error": f"规划节点异常: {str(e)}",
            "current_stage": "planning_failed",
        }
