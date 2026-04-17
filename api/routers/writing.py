from fastapi import APIRouter, Depends, HTTPException, status

from api.schemas.writing import (
    WritingRequest,
    OutlineResponse,
    DraftResponse,
    EditRequest,
    EditResponse,
    WritingProgressResponse,
)
from api.schemas.base import ResponseModel, success_response
from api.dependencies import get_session_service
from services.session_service import SessionService
from services.models import WritingRequest as WritingRequestModel
from agents.writer import WriterAgent

router = APIRouter(prefix="/writing", tags=["writing"])


@router.post("/outline", response_model=ResponseModel[OutlineResponse])
async def generate_outline(
    request: WritingRequest,
    session_service: SessionService = Depends(get_session_service),
):
    """生成大纲"""
    # 验证会话存在
    session = session_service.get_session(request.session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"会话 {request.session_id} 不存在",
        )

    # 创建写作请求
    writing_request = WritingRequestModel(
        task_type=request.task_type,
        topic=request.topic,
        audience=request.audience,
        goal=request.goal,
        tone=request.tone,
        length=request.length,
        language=request.language,
        style=request.style,
        use_rag=request.use_rag,
        use_web=request.use_web,
        extra_context=request.extra_context,
    )

    # 调用 Agent 生成大纲
    agent = WriterAgent()
    outline = await agent.generate_outline(writing_request)

    return success_response(OutlineResponse(**outline))


@router.post("/draft", response_model=ResponseModel[DraftResponse])
async def write_draft(
    request: WritingRequest,
    outline: OutlineResponse,
    session_service: SessionService = Depends(get_session_service),
):
    """生成草稿"""
    # 验证会话存在
    session = session_service.get_session(request.session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"会话 {request.session_id} 不存在",
        )

    # 调用 Agent 生成草稿
    agent = WriterAgent()
    draft = await agent.write_draft(request, outline)

    return success_response(DraftResponse(**draft))


@router.post("/edit", response_model=ResponseModel[EditResponse])
async def edit_content(
    request: EditRequest,
):
    """编辑内容"""
    agent = WriterAgent()
    result = await agent.edit(
        content=request.content,
        edit_type=request.edit_type,
        instructions=request.instructions,
    )
    return success_response(EditResponse(content=result))


@router.post("/continue", response_model=ResponseModel[DraftResponse])
async def continue_writing(
    session_id: str,
    current_content: str,
    continuation_prompt: str,
    session_service: SessionService = Depends(get_session_service),
):
    """续写"""
    # 验证会话存在
    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"会话 {session_id} 不存在",
        )

    agent = WriterAgent()
    continuation = await agent.continue_writing(
        current_content=current_content,
        prompt=continuation_prompt,
    )
    return success_response(DraftResponse(content=continuation))


@router.post("/expand", response_model=ResponseModel[DraftResponse])
async def expand_content(
    content: str,
    target_length: int,
):
    """扩写"""
    agent = WriterAgent()
    expanded = await agent.expand(content, target_length)
    return success_response(DraftResponse(content=expanded))


@router.post("/condense", response_model=ResponseModel[DraftResponse])
async def condense_content(
    content: str,
    target_length: int,
):
    """缩写"""
    agent = WriterAgent()
    condensed = await agent.condense(content, target_length)
    return success_response(DraftResponse(content=condensed))


@router.post("/polish", response_model=ResponseModel[DraftResponse])
async def polish_content(
    content: str,
    polish_type: str = "general",
):
    """润色"""
    agent = WriterAgent()
    polished = await agent.polish(content, polish_type)
    return success_response(DraftResponse(content=polished))
