"""工作流编排器

负责执行工作流，提供同步执行和流式执行两种方式。
"""

import logging
from typing import Any, AsyncGenerator, Optional

from services.models import WritingRequest
from workflows.graph import compile_quick_workflow, compile_standard_workflow
from workflows.state import WritingWorkflowState

logger = logging.getLogger(__name__)


class WritingOrchestrator:
    """写作工作流编排器

    管理工作流的生命周期，提供执行和流式执行接口。
    """

    def __init__(self, mode: str = "standard", max_iterations: int = 3):
        """
        Args:
            mode: 工作流模式，"standard" 或 "quick"
            max_iterations: 最大修改迭代次数
        """
        self.mode = mode
        self.max_iterations = max_iterations
        self._graph = None

    @property
    def graph(self):
        if self._graph is None:
            if self.mode == "quick":
                self._graph = compile_quick_workflow()
            else:
                self._graph = compile_standard_workflow()
        return self._graph

    def _build_initial_state(
        self,
        request: WritingRequest,
        user_input: Optional[str] = None,
    ) -> WritingWorkflowState:
        """从 WritingRequest 构建初始工作流状态"""
        return {
            "user_input": user_input or request.topic,
            "topic": request.topic,
            "audience": request.audience or "通用读者",
            "goal": request.goal or "信息传达",
            "tone": request.tone or "专业",
            "length": request.length or "medium",
            "style": request.style,
            "language": request.language,
            "use_rag": request.use_rag,
            "use_web": request.use_web,
            "outline": {},
            "research_notes": {},
            "draft_content": "",
            "edit_result": {},
            "review_feedback": {},
            "current_stage": "init",
            "iteration_count": 0,
            "max_iterations": self.max_iterations,
            "should_continue": False,
            "error": "",
            "final_content": "",
        }

    async def execute(
        self,
        request: WritingRequest,
        user_input: Optional[str] = None,
    ) -> WritingWorkflowState:
        """执行完整工作流，返回最终状态

        Args:
            request: 写作请求
            user_input: 用户输入文本，默认使用 request.topic

        Returns:
            最终的工作流状态
        """
        initial_state = self._build_initial_state(request, user_input)
        logger.info(f"开始执行 {self.mode} 工作流: topic={request.topic}")

        try:
            final_state = await self.graph.ainvoke(initial_state)
            logger.info(
                f"工作流执行完成: stage={final_state.get('current_stage')}, "
                f"iterations={final_state.get('iteration_count')}"
            )
            return final_state
        except Exception as e:
            logger.error(f"工作流执行失败: {e}")
            initial_state["error"] = str(e)
            initial_state["current_stage"] = "failed"
            return initial_state

    async def execute_stream(
        self,
        request: WritingRequest,
        user_input: Optional[str] = None,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """流式执行工作流，逐步返回每个阶段的状态更新

        Args:
            request: 写作请求
            user_input: 用户输入文本

        Yields:
            每个节点执行后的状态更新
        """
        initial_state = self._build_initial_state(request, user_input)
        logger.info(f"开始流式执行 {self.mode} 工作流: topic={request.topic}")

        try:
            async for event in self.graph.astream(initial_state):
                # event 格式: {node_name: state_update}
                for node_name, state_update in event.items():
                    logger.info(f"节点 {node_name} 执行完成")
                    yield {
                        "node": node_name,
                        "stage": state_update.get("current_stage", ""),
                        "update": state_update,
                    }
        except Exception as e:
            logger.error(f"流式工作流执行失败: {e}")
            yield {
                "node": "error",
                "stage": "failed",
                "update": {"error": str(e), "current_stage": "failed"},
            }

    async def resume(self, checkpoint_id: str, **kwargs) -> WritingWorkflowState:
        """从检查点恢复执行（占位符）

        TODO [CHECKPOINT]: 实现从检查点恢复工作流执行
        """
        raise NotImplementedError("检查点恢复功能尚未实现")

    async def apply_intervention(
        self, state: WritingWorkflowState, intervention: dict
    ) -> WritingWorkflowState:
        """应用用户干预（占位符）

        TODO [HUMAN_REVIEW]: 实现用户干预处理逻辑
        """
        raise NotImplementedError("用户干预功能尚未实现")
