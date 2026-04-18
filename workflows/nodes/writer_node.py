"""起草节点 - 调用 DraftAgent 生成文章初稿"""

import logging

from workflows.state import WritingWorkflowState

logger = logging.getLogger(__name__)


async def writer_node(state: WritingWorkflowState) -> dict:
    """起草节点：根据大纲和研究笔记生成文章初稿"""
    logger.info("进入起草节点")

    try:
        from agents.specialized.draft_agent import DraftAgent

        agent = DraftAgent(
            language=state.get("language", "zh"),
            style=state.get("style", "professional"),
        )

        response = await agent.execute(
            input_text=state["user_input"],
            outline=state.get("outline", {}),
            research_notes=state.get("research_notes", {}),
            tone=state.get("tone", "专业"),
        )

        if not response.success:
            return {
                "error": f"起草失败: {response.error}",
                "current_stage": "drafting_failed",
            }

        logger.info(f"初稿生成完成，字数: {len(response.content)}")
        
        current_thoughts = state.get("thoughts", [])
        current_thoughts.append({
            "node": "write",
            "content": "正在根据大纲生成文章初稿...",
        })

        return {
            "draft_content": response.content,
            "current_stage": "drafted",
            "thoughts": current_thoughts,
            "current_thought": "初稿生成完成",
            "error": "",
        }

    except Exception as e:
        logger.error(f"起草节点异常: {e}")
        return {
            "error": f"起草节点异常: {str(e)}",
            "current_stage": "drafting_failed",
        }
