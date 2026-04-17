"""评审节点 - 调用 CriticAgent 评估文章质量"""

import logging

from workflows.state import WritingWorkflowState

logger = logging.getLogger(__name__)


async def critic_node(state: WritingWorkflowState) -> dict:
    """评审节点：评估文章质量，决定是否需要继续修改"""
    logger.info("进入评审节点")

    try:
        from agents.specialized.critic_agent import CriticAgent

        agent = CriticAgent(language=state.get("language", "zh"))

        article_content = state.get("draft_content", "")
        if not article_content:
            return {
                "error": "评审节点未收到文章内容",
                "current_stage": "review_failed",
            }

        response = await agent.execute(
            input_text=article_content,
            article_content=article_content,
        )

        if not response.success:
            return {
                "error": f"评审失败: {response.error}",
                "current_stage": "review_failed",
            }

        review = response.metadata.get("review", {})
        passed = review.get("passed", False)
        iteration_count = state.get("iteration_count", 0) + 1
        max_iterations = state.get("max_iterations", 3)

        # 如果通过评审或达到最大迭代次数，结束循环
        should_continue = not passed and iteration_count < max_iterations

        logger.info(
            f"评审完成: score={review.get('overall_score', 0)}, "
            f"passed={passed}, iteration={iteration_count}/{max_iterations}"
        )

        updates = {
            "review_feedback": review,
            "current_stage": "reviewed",
            "iteration_count": iteration_count,
            "should_continue": should_continue,
            "error": "",
        }

        # 如果评审通过，设置最终内容
        if not should_continue:
            updates["final_content"] = state.get("draft_content", "")
            updates["current_stage"] = "completed"

        return updates

    except Exception as e:
        logger.error(f"评审节点异常: {e}")
        return {
            "error": f"评审节点异常: {str(e)}",
            "current_stage": "review_failed",
        }
