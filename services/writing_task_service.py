"""
写作任务服务层

提供写作任务管理的高级业务逻辑。
"""

from typing import Optional

from db.database import Database, get_db
from db.models import WritingTask as WritingTaskModel
from db.repositories import WritingTaskRepository
from services.agent_status_service import get_agent_status_service


class WritingTaskService:
    """
    写作任务服务

    管理写作任务的创建、状态跟踪和结果管理。
    """

    def __init__(self, db: Optional[Database] = None):
        self.db = db or get_db()
        self.task_repo = WritingTaskRepository(self.db)

    def create_task(
        self,
        session_id: str,
        task_type: str,
        topic: str,
        request: Optional[dict] = None,
        document_id: Optional[str] = None,
    ) -> WritingTaskModel:
        """
        创建写作任务

        Args:
            session_id: 会话 ID
            task_type: 任务类型
            topic: 主题
            request: 请求详情
            document_id: 关联文档 ID

        Returns:
            WritingTaskModel: 创建的任务
        """
        task = WritingTaskModel(
            session_id=session_id,
            document_id=document_id,
            task_type=task_type,
            topic=topic,
            request=request or {},
            status="pending",
        )
        return self.task_repo.create(task)

    def get_task(self, task_id: str) -> Optional[WritingTaskModel]:
        """
        获取任务

        Args:
            task_id: 任务 ID

        Returns:
            Optional[WritingTaskModel]: 任务对象
        """
        return self.task_repo.get_by_id(task_id)

    def get_session_tasks(self, session_id: str) -> list[WritingTaskModel]:
        """
        获取会话的所有任务

        Args:
            session_id: 会话 ID

        Returns:
            list[WritingTaskModel]: 任务列表
        """
        return self.task_repo.get_by_session_id(session_id)

    def get_document_tasks(self, document_id: str) -> list[WritingTaskModel]:
        """
        获取文档的所有任务

        Args:
            document_id: 文档 ID

        Returns:
            list[WritingTaskModel]: 任务列表
        """
        return self.task_repo.get_by_document_id(document_id)

    def start_task(self, task_id: str) -> bool:
        """
        开始任务

        Args:
            task_id: 任务 ID

        Returns:
            bool: 是否成功
        """
        return self.task_repo.update_status(task_id, "running")

    def update_task_state(self, task_id: str, state: dict) -> Optional[WritingTaskModel]:
        """
        更新任务状态

        Args:
            task_id: 任务 ID
            state: 状态数据

        Returns:
            Optional[WritingTaskModel]: 更新后的任务
        """
        task = self.task_repo.get_by_id(task_id)
        if task:
            task.state.update(state)
            return self.task_repo.update(task)
        return None

    def complete_task(self, task_id: str, result: str) -> bool:
        """
        完成任务

        Args:
            task_id: 任务 ID
            result: 结果内容

        Returns:
            bool: 是否成功
        """
        return self.task_repo.complete_task(task_id, result)

    def fail_task(self, task_id: str, error_message: str) -> bool:
        """
        标记任务失败

        Args:
            task_id: 任务 ID
            error_message: 错误信息

        Returns:
            bool: 是否成功
        """
        return self.task_repo.fail_task(task_id, error_message)

    def list_pending_tasks(self, limit: int = 100) -> list[WritingTaskModel]:
        """
        获取待处理任务

        Args:
            limit: 限制数量

        Returns:
            list[WritingTaskModel]: 任务列表
        """
        return self.task_repo.list_by_status("pending", limit)

    def list_running_tasks(self, limit: int = 100) -> list[WritingTaskModel]:
        """
        获取运行中任务

        Args:
            limit: 限制数量

        Returns:
            list[WritingTaskModel]: 任务列表
        """
        return self.task_repo.list_by_status("running", limit)

    def list_completed_tasks(self, limit: int = 100) -> list[WritingTaskModel]:
        """
        获取已完成任务

        Args:
            limit: 限制数量

        Returns:
            list[WritingTaskModel]: 任务列表
        """
        return self.task_repo.list_by_status("completed", limit)

    def list_failed_tasks(self, limit: int = 100) -> list[WritingTaskModel]:
        """
        获取失败任务

        Args:
            limit: 限制数量

        Returns:
            list[WritingTaskModel]: 任务列表
        """
        return self.task_repo.list_by_status("failed", limit)

    def delete_task(self, task_id: str) -> bool:
        """
        删除任务

        Args:
            task_id: 任务 ID

        Returns:
            bool: 是否成功
        """
        return self.task_repo.delete(task_id)

    def retry_task(self, task_id: str) -> Optional[WritingTaskModel]:
        """
        重试失败任务

        Args:
            task_id: 任务 ID

        Returns:
            Optional[WritingTaskModel]: 新创建的任务
        """
        old_task = self.task_repo.get_by_id(task_id)
        if not old_task or old_task.status != "failed":
            return None

        # 创建新任务
        new_task = WritingTaskModel(
            session_id=old_task.session_id,
            document_id=old_task.document_id,
            task_type=old_task.task_type,
            topic=old_task.topic,
            request=old_task.request,
            status="pending",
        )
        return self.task_repo.create(new_task)

    async def execute_and_stream(self, task_id: str, request: dict) -> None:
        """执行工作流并通过 SSE 推送状态

        Args:
            task_id: 任务 ID
            request: 写作请求字典
        """
        self.start_task(task_id)
        status_service = get_agent_status_service()

        try:
            from services.models import WritingRequest
            from workflows.orchestrator import WritingOrchestrator

            writing_request = WritingRequest.from_dict(request)
            orchestrator = WritingOrchestrator(mode="standard")

            async for update in orchestrator.execute_stream(writing_request):
                await status_service.publish_progress(
                    task_id=task_id,
                    node=update.get("node", ""),
                    stage=update.get("stage", ""),
                    thoughts=update.get("thoughts", []),
                    preview=update.get("preview", ""),
                )

                if update["stage"] in ["completed", "failed"]:
                    if update["stage"] == "completed":
                        final_content = update.get("update", {}).get("final_content", "")
                        stage_history = update.get("update", {}).get("stage_history", [])
                        await status_service.publish_complete(
                            task_id=task_id,
                            final_content=final_content,
                            stage_history=stage_history,
                        )
                        self.complete_task(task_id, final_content)
                    else:
                        error = update.get("update", {}).get("error", "未知错误")
                        await status_service.publish_error(task_id=task_id, error=error)
                        self.fail_task(task_id, error)
                    break
        except Exception as e:
            await status_service.publish_error(task_id=task_id, error=str(e))
            self.fail_task(task_id, str(e))

    def get_task_stats(self) -> dict:
        """获取任务统计信息

        Returns:
            dict: 统计信息
        """
        pending = len(self.task_repo.list_by_status("pending", 10000))
        running = len(self.task_repo.list_by_status("running", 10000))
        completed = len(self.task_repo.list_by_status("completed", 10000))
        failed = len(self.task_repo.list_by_status("failed", 10000))

        return {
            "pending": pending,
            "running": running,
            "completed": completed,
            "failed": failed,
            "total": pending + running + completed + failed,
        }


# 全局服务实例
_task_service: Optional[WritingTaskService] = None


def get_writing_task_service(db: Optional[Database] = None) -> WritingTaskService:
    """获取全局 WritingTaskService 实例"""
    global _task_service
    if _task_service is None:
        _task_service = WritingTaskService(db)
    return _task_service
