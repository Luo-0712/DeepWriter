from typing import Generic, TypeVar, Optional
from pydantic import BaseModel

T = TypeVar('T')


class ResponseModel(BaseModel, Generic[T]):
    """统一响应模型"""
    success: bool = True
    data: Optional[T] = None
    message: Optional[str] = None
    error: Optional[dict] = None


def success_response(data: T = None, message: str = None) -> ResponseModel[T]:
    """成功响应"""
    return ResponseModel(
        success=True,
        data=data,
        message=message,
    )


def error_response(code: int, message: str, details: dict = None) -> ResponseModel:
    """错误响应"""
    return ResponseModel(
        success=False,
        error={
            "code": code,
            "message": message,
            "details": details,
        },
    )
