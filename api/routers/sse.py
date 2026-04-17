from fastapi import APIRouter, Depends, HTTPException
from sse_starlette.sse import EventSourceResponse
import json
import asyncio

from api.dependencies import get_session_service, get_task_service
from services.session_service import SessionService
from services.writing_task_service import WritingTaskService
from api.utils.sse_manager import sse_manager

router = APIRouter(prefix="/sse", tags=["sse"])


@router.get("/chat/{session_id}")
async def chat_stream(
    session_id: str,
    message: str,
    session_service: SessionService = Depends(get_session_service),
):
    """对话流式响应 (SSE)"""
    # 验证会话存在
    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"会话 {session_id} 不存在")

    from agents.writer import WriterAgent
    from services.message_service import get_message_service

    message_service = get_message_service()

    # 保存用户消息
    message_service.add_user_message(session_id, message)

    agent = WriterAgent()

    async def event_generator():
        full_content = ""
        async for chunk in agent.astream_chat(session_id, message):
            full_content += chunk
            yield {
                "event": "message",
                "data": json.dumps({
                    "content": chunk,
                    "is_end": False,
                }),
            }

        # 保存完整回复
        message_service.add_assistant_message(session_id, full_content)

        # 发送结束标记
        yield {
            "event": "message",
            "data": json.dumps({
                "content": "",
                "is_end": True,
            }),
        }

    return EventSourceResponse(event_generator())


@router.get("/tasks/{task_id}/progress")
async def task_progress_stream(
    task_id: str,
    task_service: WritingTaskService = Depends(get_task_service),
):
    """任务进度流式推送 (SSE)"""
    # 验证任务存在
    task = task_service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"任务 {task_id} 不存在")

    async def event_generator():
        queue = await sse_manager.subscribe(task_id)
        try:
            while True:
                try:
                    # 设置超时，避免无限等待
                    message = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield {
                        "event": message.get("event", "progress"),
                        "data": json.dumps(message.get("data", {})),
                    }
                    # 如果任务完成，结束流
                    if message.get("event") == "complete":
                        break
                except asyncio.TimeoutError:
                    # 发送心跳保持连接
                    yield {
                        "event": "heartbeat",
                        "data": json.dumps({"timestamp": asyncio.get_event_loop().time()}),
                    }
        finally:
            await sse_manager.unsubscribe(task_id, queue)

    return EventSourceResponse(event_generator())
