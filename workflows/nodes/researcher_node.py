"""研究节点 - 调用 ResearcherAgent 收集和整理研究资料"""

import logging
import time
from typing import Optional

from langchain_core.tools import BaseTool

from workflows.state import WritingWorkflowState

logger = logging.getLogger(__name__)


def _build_tools(use_rag: bool, use_web: bool) -> list[BaseTool]:
    """根据配置构建工具列表"""
    tools = []
    if use_web:
        try:
            from tools.search import get_search_tool
            tools.append(get_search_tool())
        except Exception as e:
            logger.warning(f"搜索工具初始化失败: {e}")

    if use_rag:
        try:
            from tools.rag_retrieval import get_rag_retrieval_tool
            tools.append(get_rag_retrieval_tool())
        except Exception as e:
            logger.warning(f"RAG 工具初始化失败: {e}")

    return tools


async def researcher_node(state: WritingWorkflowState) -> dict:
    """研究节点：根据大纲收集研究资料"""
    logger.info("进入研究节点")

    try:
        from agents.specialized.researcher_agent import ResearcherAgent

        use_rag = state.get("use_rag", False)
        use_web = state.get("use_web", False)
        tools = _build_tools(use_rag, use_web)

        agent = ResearcherAgent(
            language=state.get("language", "zh"),
            tools=tools,
        )

        response = await agent.execute(
            input_text=state["user_input"],
            outline=state.get("outline", {}),
            use_rag=use_rag,
            use_web=use_web,
        )

        if not response.success:
            return {
                "error": f"研究失败: {response.error}",
                "current_stage": "research_failed",
            }

        research_notes = response.metadata.get("research_notes", {"raw_content": response.content})

        logger.info("研究资料收集完成")
        
        current_thoughts = state.get("thoughts", [])
        current_thoughts.append({
            "node": "research",
            "content": "正在进行资料检索和整理...",
        })

        stage_history = state.get("stage_history", [])
        stage_history.append({
            "stage": "researched",
            "timestamp": time.time(),
        })

        return {
            "research_notes": research_notes,
            "current_stage": "researched",
            "thoughts": current_thoughts,
            "current_thought": "研究资料收集完成",
            "stage_history": stage_history,
            "research_preview": response.content[:500] if len(response.content) > 500 else response.content,
            "error": "",
        }

    except Exception as e:
        logger.error(f"研究节点异常: {e}")
        return {
            "error": f"研究节点异常: {str(e)}",
            "current_stage": "research_failed",
        }
