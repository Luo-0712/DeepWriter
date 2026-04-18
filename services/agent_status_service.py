"""智能体状态推送服务

负责向 SSE 频道推送智能体执行状态、思考过程等实时信息。
"""

import time
from typing import Optional

from api.utils.sse_manager import sse_manager


class AgentStatusService:
    """智能体状态推送服务"""

    async def publish_stage_update(
        self, task_id: str, stage: str, thought: str
    ) -> None:
        """推送阶段更新到 SSE

        Args:
            task_id: 任务 ID
            stage: 当前阶段名称
            thought: 当前思考内容
        """
        await sse_manager.publish(task_id, {
            "event": "stage_update",
            "data": {
                "stage": stage,
                "thought": thought,
                "timestamp": time.time(),
            },
        })

    async def publish_thinking(self, task_id: str, content: str) -> None:
        """推送思考过程

        Args:
            task_id: 任务 ID
            content: 思考内容
        """
        await sse_manager.publish(task_id, {
            "event": "thinking",
            "data": {"content": content, "timestamp": time.time()},
        })

    async def publish_progress(
        self, task_id: str, node: str, stage: str, thoughts: list, preview: str = ""
    ) -> None:
        """推送节点执行进度

        Args:
            task_id: 任务 ID
            node: 节点名称
            stage: 阶段名称
            thoughts: 思考过程列表
            preview: 预览内容
        """
        await sse_manager.publish(task_id, {
            "event": "progress",
            "data": {
                "node": node,
                "stage": stage,
                "thoughts": thoughts,
                "preview": preview,
                "timestamp": time.time(),
            },
        })

    async def publish_complete(
        self, task_id: str, final_content: str, stage_history: list
    ) -> None:
        """推送任务完成事件

        Args:
            task_id: 任务 ID
            final_content: 最终生成内容
            stage_history: 阶段历史
        """
        await sse_manager.publish(task_id, {
            "event": "complete",
            "data": {
                "final_content": final_content,
                "stage_history": stage_history,
                "timestamp": time.time(),
            },
        })

    async def publish_error(self, task_id: str, error: str) -> None:
        """推送错误事件

        Args:
            task_id: 任务 ID
            error: 错误信息
        """
        await sse_manager.publish(task_id, {
            "event": "error",
            "data": {"error": error, "timestamp": time.time()},
        })


_agent_status_service: Optional[AgentStatusService] = None


def get_agent_status_service() -> AgentStatusService:
    """获取全局 AgentStatusService 实例"""
    global _agent_status_service
    if _agent_status_service is None:
        _agent_status_service = AgentStatusService()
    return _agent_status_service
