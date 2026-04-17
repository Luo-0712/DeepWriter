from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional

from api.schemas.task import (
    TaskCreateRequest,
    TaskResponse,
    TaskListResponse,
    TaskStatsResponse,
)
from api.schemas.base import ResponseModel, success_response
from api.dependencies import get_task_service, get_session_service
from services.writing_task_service import WritingTaskService
from services.session_service import SessionService

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("", response_model=ResponseModel[TaskListResponse])
async def list_tasks(
    session_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    task_service: WritingTaskService = Depends(get_task_service),
):
    """获取任务列表"""
    if session_id:
        tasks = task_service.get_session_tasks(session_id)
    elif status:
        if status == "pending":
            tasks = task_service.list_pending_tasks(limit)
        elif status == "running":
            tasks = task_service.list_running_tasks(limit)
        elif status == "completed":
            tasks = task_service.list_completed_tasks(limit)
        elif status == "failed":
            tasks = task_service.list_failed_tasks(limit)
        else:
            tasks = []
    else:
        # 获取所有任务
        tasks = []

    return success_response(
        TaskListResponse(
            total=len(tasks),
            items=[TaskResponse.model_validate(t) for t in tasks],
        )
    )


@router.post("", response_model=ResponseModel[TaskResponse], status_code=status.HTTP_201_CREATED)
async def create_task(
    request: TaskCreateRequest,
    task_service: WritingTaskService = Depends(get_task_service),
    session_service: SessionService = Depends(get_session_service),
):
    """创建任务"""
    # 验证会话存在
    session = session_service.get_session(request.session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"会话 {request.session_id} 不存在",
        )

    task = task_service.create_task(
        session_id=request.session_id,
        task_type=request.task_type,
        topic=request.topic,
        request=request.request,
        document_id=request.document_id,
    )
    return success_response(
        TaskResponse.model_validate(task),
        message="任务创建成功",
    )


@router.get("/{task_id}", response_model=ResponseModel[TaskResponse])
async def get_task(
    task_id: str,
    task_service: WritingTaskService = Depends(get_task_service),
):
    """获取任务详情"""
    task = task_service.get_task(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"任务 {task_id} 不存在",
        )
    return success_response(TaskResponse.model_validate(task))


@router.post("/{task_id}/start", response_model=ResponseModel[TaskResponse])
async def start_task(
    task_id: str,
    task_service: WritingTaskService = Depends(get_task_service),
):
    """开始任务"""
    success = task_service.start_task(task_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="任务启动失败",
        )
    task = task_service.get_task(task_id)
    return success_response(
        TaskResponse.model_validate(task),
        message="任务已开始",
    )


@router.post("/{task_id}/cancel", response_model=ResponseModel[TaskResponse])
async def cancel_task(
    task_id: str,
    task_service: WritingTaskService = Depends(get_task_service),
):
    """取消任务"""
    # TODO: 实现取消任务逻辑
    task = task_service.get_task(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"任务 {task_id} 不存在",
        )
    return success_response(TaskResponse.model_validate(task))


@router.post("/{task_id}/retry", response_model=ResponseModel[TaskResponse])
async def retry_task(
    task_id: str,
    task_service: WritingTaskService = Depends(get_task_service),
):
    """重试任务"""
    new_task = task_service.retry_task(task_id)
    if not new_task:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="任务重试失败",
        )
    return success_response(
        TaskResponse.model_validate(new_task),
        message="任务已重试",
    )


@router.delete("/{task_id}", response_model=ResponseModel[dict])
async def delete_task(
    task_id: str,
    task_service: WritingTaskService = Depends(get_task_service),
):
    """删除任务"""
    success = task_service.delete_task(task_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"任务 {task_id} 不存在",
        )
    return success_response({"deleted": True}, message="任务删除成功")


@router.get("/stats/summary", response_model=ResponseModel[TaskStatsResponse])
async def get_task_stats(
    task_service: WritingTaskService = Depends(get_task_service),
):
    """获取任务统计"""
    stats = task_service.get_task_stats()
    return success_response(TaskStatsResponse(**stats))
