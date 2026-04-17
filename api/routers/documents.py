from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional

from api.schemas.document import (
    DocumentCreateRequest,
    DocumentUpdateRequest,
    DocumentResponse,
    DocumentListResponse,
    DocumentVersionResponse,
    DocumentVersionListResponse,
)
from api.schemas.base import ResponseModel, success_response
from api.dependencies import get_document_service, get_session_service
from services.document_service import DocumentService
from services.session_service import SessionService

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("", response_model=ResponseModel[DocumentListResponse])
async def list_documents(
    session_id: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    document_service: DocumentService = Depends(get_document_service),
):
    """获取文档列表"""
    if session_id:
        documents = document_service.get_session_documents(session_id)
    else:
        # TODO: 实现获取所有文档的方法
        documents = []

    return success_response(
        DocumentListResponse(
            total=len(documents),
            items=[DocumentResponse.model_validate(d) for d in documents],
        )
    )


@router.post("", response_model=ResponseModel[DocumentResponse], status_code=status.HTTP_201_CREATED)
async def create_document(
    request: DocumentCreateRequest,
    document_service: DocumentService = Depends(get_document_service),
    session_service: SessionService = Depends(get_session_service),
):
    """创建文档"""
    # 验证会话存在
    session = session_service.get_session(request.session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"会话 {request.session_id} 不存在",
        )

    document = document_service.create_document(
        session_id=request.session_id,
        title=request.title,
        content=request.content,
        doc_type=request.doc_type,
        metadata=request.metadata,
    )
    return success_response(
        DocumentResponse.model_validate(document),
        message="文档创建成功",
    )


@router.get("/{document_id}", response_model=ResponseModel[DocumentResponse])
async def get_document(
    document_id: str,
    document_service: DocumentService = Depends(get_document_service),
):
    """获取文档详情"""
    document = document_service.get_document(document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"文档 {document_id} 不存在",
        )
    return success_response(DocumentResponse.model_validate(document))


@router.put("/{document_id}", response_model=ResponseModel[DocumentResponse])
async def update_document(
    document_id: str,
    request: DocumentUpdateRequest,
    document_service: DocumentService = Depends(get_document_service),
):
    """更新文档"""
    document = document_service.update_document(
        document_id=document_id,
        title=request.title,
        content=request.content,
        create_version=request.create_version,
        change_summary=request.change_summary,
    )
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"文档 {document_id} 不存在",
        )
    return success_response(
        DocumentResponse.model_validate(document),
        message="文档更新成功",
    )


@router.delete("/{document_id}", response_model=ResponseModel[dict])
async def delete_document(
    document_id: str,
    document_service: DocumentService = Depends(get_document_service),
):
    """删除文档"""
    success = document_service.delete_document(document_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"文档 {document_id} 不存在",
        )
    return success_response({"deleted": True}, message="文档删除成功")


@router.post("/{document_id}/versions", response_model=ResponseModel[DocumentVersionResponse])
async def create_version(
    document_id: str,
    change_summary: str,
    document_service: DocumentService = Depends(get_document_service),
):
    """创建文档版本"""
    version = document_service.create_version(document_id, change_summary)
    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"文档 {document_id} 不存在",
        )
    return success_response(
        DocumentVersionResponse.model_validate(version),
        message="版本创建成功",
    )


@router.get("/{document_id}/versions", response_model=ResponseModel[DocumentVersionListResponse])
async def list_versions(
    document_id: str,
    document_service: DocumentService = Depends(get_document_service),
):
    """获取文档版本列表"""
    versions = document_service.get_document_versions(document_id)
    return success_response(
        DocumentVersionListResponse(
            total=len(versions),
            items=[DocumentVersionResponse.model_validate(v) for v in versions],
        )
    )


@router.post("/{document_id}/restore", response_model=ResponseModel[DocumentResponse])
async def restore_version(
    document_id: str,
    version_number: int,
    document_service: DocumentService = Depends(get_document_service),
):
    """恢复到指定版本"""
    document = document_service.restore_version(document_id, version_number)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"文档或版本不存在",
        )
    return success_response(
        DocumentResponse.model_validate(document),
        message=f"已恢复到版本 {version_number}",
    )


@router.post("/{document_id}/publish", response_model=ResponseModel[DocumentResponse])
async def publish_document(
    document_id: str,
    document_service: DocumentService = Depends(get_document_service),
):
    """发布文档"""
    success = document_service.publish_document(document_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"文档 {document_id} 不存在",
        )
    document = document_service.get_document(document_id)
    return success_response(
        DocumentResponse.model_validate(document),
        message="文档已发布",
    )
