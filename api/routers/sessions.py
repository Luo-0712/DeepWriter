from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional

from api.schemas.session import (
    SessionCreateRequest,
    SessionUpdateRequest,
    SessionResponse,
    SessionListResponse,
    SessionStatsResponse,
)
from api.schemas.base import ResponseModel, success_response
from api.dependencies import get_session_service
from services.session_service import SessionService

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.get("", response_model=ResponseModel[SessionListResponse])
async def list_sessions(
    limit: int = 100,
    offset: int = 0,
    session_service: SessionService = Depends(get_session_service),
):
    """获取会话列表"""
    sessions = session_service.list_all_sessions(limit, offset)
    return success_response(
        SessionListResponse(
            total=len(sessions),
            items=[SessionResponse.model_validate(s) for s in sessions],
        )
    )


@router.post("", response_model=ResponseModel[SessionResponse], status_code=status.HTTP_201_CREATED)
async def create_session(
    request: SessionCreateRequest,
    session_service: SessionService = Depends(get_session_service),
):
    """创建新会话"""
    session = session_service.create_session(
        title=request.title,
        config=request.config,
    )
    return success_response(
        SessionResponse.model_validate(session),
        message="会话创建成功",
    )


@router.get("/{session_id}", response_model=ResponseModel[SessionResponse])
async def get_session(
    session_id: str,
    session_service: SessionService = Depends(get_session_service),
):
    """获取会话详情"""
    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"会话 {session_id} 不存在",
        )
    return success_response(SessionResponse.model_validate(session))


@router.put("/{session_id}", response_model=ResponseModel[SessionResponse])
async def update_session(
    session_id: str,
    request: SessionUpdateRequest,
    session_service: SessionService = Depends(get_session_service),
):
    """更新会话"""
    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"会话 {session_id} 不存在",
        )
    if request.title:
        session.title = request.title
    if request.config:
        session.config.update(request.config)
    updated = session_service.update_session(session)
    return success_response(
        SessionResponse.model_validate(updated),
        message="会话更新成功",
    )


@router.delete("/{session_id}", response_model=ResponseModel[dict])
async def delete_session(
    session_id: str,
    session_service: SessionService = Depends(get_session_service),
):
    """删除会话"""
    success = session_service.delete_session(session_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"会话 {session_id} 不存在",
        )
    return success_response({"deleted": True}, message="会话删除成功")


@router.post("/{session_id}/archive", response_model=ResponseModel[SessionResponse])
async def archive_session(
    session_id: str,
    session_service: SessionService = Depends(get_session_service),
):
    """归档会话"""
    success = session_service.archive_session(session_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"会话 {session_id} 不存在",
        )
    session = session_service.get_session(session_id)
    return success_response(
        SessionResponse.model_validate(session),
        message="会话已归档",
    )


@router.get("/{session_id}/stats", response_model=ResponseModel[SessionStatsResponse])
async def get_session_stats(
    session_id: str,
    session_service: SessionService = Depends(get_session_service),
):
    """获取会话统计"""
    stats = session_service.get_session_stats(session_id)
    return success_response(SessionStatsResponse(**stats))
