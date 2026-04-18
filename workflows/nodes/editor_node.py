"""编辑节点 - 调用 EditorAgent 审查和改进草稿"""

import logging

from workflows.state import WritingWorkflowState

logger = logging.getLogger(__name__)


async def editor_node(state: WritingWorkflowState) -> dict:
    """编辑节点：审查草稿并给出修改建议"""
    logger.info("进入编辑节点")

    try:
        from agents.specialized.editor_agent import EditorAgent

        agent = EditorAgent(language=state.get("language", "zh"))

        draft_content = state.get("draft_content", "")
        if not draft_content:
            return {
                "error": "编辑节点未收到草稿内容",
                "current_stage": "editing_failed",
            }

        response = await agent.execute(
            input_text=draft_content,
            draft_content=draft_content,
        )

        if not response.success:
            return {
                "error": f"编辑失败: {response.error}",
                "current_stage": "editing_failed",
            }

        edit_result = response.metadata.get("edit_result", {})

        # 如果编辑器返回了修改后的内容，更新 draft_content
        revised_content = edit_result.get("revised_content", "")
        updates = {
            "edit_result": edit_result,
            "current_stage": "edited",
            "error": "",
        }
        if revised_content:
            updates["draft_content"] = revised_content

        current_thoughts = state.get("thoughts", [])
        current_thoughts.append({
            "node": "edit",
            "content": "正在审查草稿内容，优化语言表达和逻辑结构...",
        })

        updates["thoughts"] = current_thoughts
        updates["current_thought"] = "编辑审查完成"

        logger.info("编辑审查完成")
        return updates

    except Exception as e:
        logger.error(f"编辑节点异常: {e}")
        return {
            "error": f"编辑节点异常: {str(e)}",
            "current_stage": "editing_failed",
        }
