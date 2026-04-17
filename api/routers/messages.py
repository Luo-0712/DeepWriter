from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional

from api.schemas.message import (
    MessageCreateRequest,
    MessageResponse,
    MessageListResponse,
    ChatRequest,
    ChatResponse,
)
from api.schemas.base import ResponseModel, success_response
from api.dependencies import get_message_service, get_session_service
from services.message_service import MessageService
from services.session_service import SessionService

router = APIRouter(tags=["messages"])


@router.get("/sessions/{session_id}/messages", response_model=ResponseModel[MessageListResponse])
async def list_messages(
    session_id: str,
    limit: int = 100,
    offset: int = 0,
    message_service: MessageService = Depends(get_message_service),
    session_service: SessionService = Depends(get_session_service),
):
    """获取会话消息列表"""
    # 验证会话存在
    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"会话 {session_id} 不存在",
        )

    messages = message_service.get_session_messages(session_id, limit, offset)
    return success_response(
        MessageListResponse(
            total=len(messages),
            items=[MessageResponse.model_validate(m) for m in messages],
        )
    )


@router.post("/sessions/{session_id}/messages", response_model=ResponseModel[MessageResponse])
async def create_message(
    session_id: str,
    request: MessageCreateRequest,
    message_service: MessageService = Depends(get_message_service),
    session_service: SessionService = Depends(get_session_service),
):
    """发送消息"""
    # 验证会话存在
    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"会话 {session_id} 不存在",
        )

    message = message_service.create_message(
        session_id=session_id,
        role=request.role,
        content=request.content,
        metadata=request.metadata,
    )
    return success_response(
        MessageResponse.model_validate(message),
        message="消息发送成功",
    )


@router.delete("/sessions/{session_id}/messages", response_model=ResponseModel[dict])
async def clear_messages(
    session_id: str,
    message_service: MessageService = Depends(get_message_service),
    session_service: SessionService = Depends(get_session_service),
):
    """清空会话消息"""
    # 验证会话存在
    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"会话 {session_id} 不存在",
        )

    count = message_service.clear_session_messages(session_id)
    return success_response({"deleted_count": count}, message="消息已清空")


@router.get("/sessions/{session_id}/messages/history", response_model=ResponseModel[list[dict]])
async def get_chat_history(
    session_id: str,
    limit: int = 10,
    message_service: MessageService = Depends(get_message_service),
    session_service: SessionService = Depends(get_session_service),
):
    """获取聊天历史（用于 LLM 上下文）"""
    # 验证会话存在
    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"会话 {session_id} 不存在",
        )

    history = message_service.get_chat_history(session_id, limit)
    return success_response(history)


@router.post("/sessions/{session_id}/chat", response_model=ResponseModel[ChatResponse])
async def chat(
    session_id: str,
    request: ChatRequest,
    message_service: MessageService = Depends(get_message_service),
    session_service: SessionService = Depends(get_session_service),
):
    """对话接口（非流式）"""
    from agents.writer import WriterAgent

    # 验证会话存在
    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"会话 {session_id} 不存在",
        )

    # 保存用户消息
    message_service.add_user_message(session_id, request.message)

    # 调用 Agent 生成回复
    agent = WriterAgent()
    response_content = await agent.execute(request.message)

    # 保存助手消息
    message_service.add_assistant_message(session_id, response_content.content)

    return success_response(
        ChatResponse(
            message=response_content.content,
            session_id=session_id,
        ),
        message="对话成功",
    )
