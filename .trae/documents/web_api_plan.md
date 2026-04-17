# DeepWriter Web API 开发计划

## 1. 项目概述

### 1.1 目标
基于 FastAPI 构建完整的 RESTful API 控制层，为前端提供统一的接口服务，支持 DeepWriter 的所有核心功能。

### 1.2 技术栈
- **Web 框架**: FastAPI (异步高性能)
- **数据验证**: Pydantic v2
- **数据库**: SQLite (开发) / PostgreSQL (生产)
- **文档**: OpenAPI/Swagger (自动生成)
- **CORS**: 支持跨域请求
- **实时推送**: Server-Sent Events (SSE)

---

## 2. 架构设计

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (React/Vue)                     │
└───────────────────────────────┬─────────────────────────────────┘
                                │ HTTP / SSE
┌───────────────────────────────▼─────────────────────────────────┐
│                      FastAPI Application                        │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  API Layer (Routers)                                    │   │
│  │  ├── sessions.py      # 会话管理                        │   │
│  │  ├── messages.py      # 消息对话                        │   │
│  │  ├── documents.py     # 文档管理                        │   │
│  │  ├── tasks.py         # 写作任务                        │   │
│  │  ├── knowledge.py     # 知识库管理                      │   │
│  │  ├── writing.py       # 写作流程                        │   │
│  │  └── sse.py           # SSE 实时推送                    │   │
│  └─────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Service Layer (Controllers)                            │   │
│  │  ├── session_controller.py                            │   │
│  │  ├── writing_controller.py                            │   │
│  │  ├── document_controller.py                           │   │
│  │  └── task_controller.py                               │   │
│  └─────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Business Layer (Existing Services)                     │   │
│  │  ├── SessionService                                   │   │
│  │  ├── MessageService                                   │   │
│  │  ├── DocumentService                                  │   │
│  │  └── WritingTaskService                               │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 目录结构

```
api/
├── __init__.py
├── main.py                 # FastAPI 应用入口
├── config.py              # API 配置
├── dependencies.py        # 依赖注入
├── middlewares/           # 中间件
│   ├── __init__.py
│   ├── cors.py           # CORS 配置
│   ├── error_handler.py  # 错误处理
│   └── logging.py        # 请求日志
├── routers/               # 路由层
│   ├── __init__.py
│   ├── sessions.py       # 会话路由
│   ├── messages.py       # 消息路由
│   ├── documents.py      # 文档路由
│   ├── tasks.py          # 任务路由
│   ├── knowledge.py      # 知识库路由
│   ├── writing.py        # 写作流程路由
│   └── sse.py            # SSE 实时推送路由
├── controllers/           # 控制层
│   ├── __init__.py
│   ├── base.py           # 控制器基类
│   ├── session_controller.py
│   ├── writing_controller.py
│   ├── document_controller.py
│   └── task_controller.py
├── schemas/               # Pydantic 模型
│   ├── __init__.py
│   ├── base.py           # 基础响应模型
│   ├── session.py        # 会话相关
│   ├── message.py        # 消息相关
│   ├── document.py       # 文档相关
│   ├── task.py           # 任务相关
│   ├── writing.py        # 写作相关
│   └── knowledge.py      # 知识库相关
└── utils/                 # 工具函数
    ├── __init__.py
├── response.py       # 统一响应格式
    ├── exceptions.py     # 自定义异常
    └── sse_manager.py    # SSE 连接管理
```

---

## 3. API 设计

### 3.1 会话模块 (Sessions)

```python
# GET    /api/v1/sessions               # 获取会话列表
# POST   /api/v1/sessions               # 创建新会话
# GET    /api/v1/sessions/{id}          # 获取会话详情
# PUT    /api/v1/sessions/{id}          # 更新会话
# DELETE /api/v1/sessions/{id}          # 删除会话
# POST   /api/v1/sessions/{id}/archive  # 归档会话
# GET    /api/v1/sessions/{id}/stats    # 获取会话统计
```

**Schema:**
```python
class SessionCreateRequest(BaseModel):
    title: Optional[str] = "新会话"
    config: Optional[dict] = {}

class SessionUpdateRequest(BaseModel):
    title: Optional[str] = None
    config: Optional[dict] = None

class SessionResponse(BaseModel):
    id: str
    title: str
    status: str
    message_count: int
    document_count: int
    created_at: datetime
    updated_at: datetime

class SessionListResponse(BaseModel):
    total: int
    items: list[SessionResponse]
```

### 3.2 消息模块 (Messages)

```python
# GET    /api/v1/sessions/{id}/messages           # 获取消息列表
# POST   /api/v1/sessions/{id}/messages           # 发送消息
# DELETE /api/v1/sessions/{id}/messages           # 清空消息
# GET    /api/v1/sessions/{id}/messages/history   # 获取聊天历史
```

**Schema:**
```python
class MessageCreateRequest(BaseModel):
    content: str = Field(..., min_length=1)
    metadata: Optional[dict] = {}

class MessageResponse(BaseModel):
    id: int
    session_id: str
    role: str
    content: str
    metadata: dict
    created_at: datetime

class ChatRequest(BaseModel):
    message: str
    stream: bool = False  # 是否流式响应
```

### 3.3 文档模块 (Documents)

```python
# GET    /api/v1/documents                    # 获取文档列表
# POST   /api/v1/documents                    # 创建文档
# GET    /api/v1/documents/{id}               # 获取文档详情
# PUT    /api/v1/documents/{id}               # 更新文档
# DELETE /api/v1/documents/{id}               # 删除文档
# POST   /api/v1/documents/{id}/versions      # 创建版本
# GET    /api/v1/documents/{id}/versions      # 获取版本列表
# POST   /api/v1/documents/{id}/restore       # 恢复到版本
# POST   /api/v1/documents/{id}/publish       # 发布文档
```

**Schema:**
```python
class DocumentCreateRequest(BaseModel):
    session_id: str
    title: str
    content: Optional[str] = ""
    doc_type: Optional[str] = "article"
    metadata: Optional[dict] = {}

class DocumentUpdateRequest(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    create_version: bool = False
    change_summary: Optional[str] = None

class DocumentResponse(BaseModel):
    id: str
    session_id: str
    title: str
    content: str
    doc_type: str
    status: str
    version_count: int
    created_at: datetime
    updated_at: datetime
```

### 3.4 写作任务模块 (Tasks)

```python
# GET    /api/v1/tasks                  # 获取任务列表
# POST   /api/v1/tasks                  # 创建任务
# GET    /api/v1/tasks/{id}             # 获取任务详情
# POST   /api/v1/tasks/{id}/start       # 开始任务
# POST   /api/v1/tasks/{id}/cancel      # 取消任务
# POST   /api/v1/tasks/{id}/retry       # 重试任务
# DELETE /api/v1/tasks/{id}             # 删除任务
# GET    /api/v1/tasks/stats            # 获取任务统计
```

**Schema:**
```python
class TaskCreateRequest(BaseModel):
    session_id: str
    task_type: str
    topic: str
    request: Optional[dict] = {}
    document_id: Optional[str] = None

class TaskResponse(BaseModel):
    id: str
    session_id: str
    task_type: str
    topic: str
    status: str
    progress: Optional[float] = None
    result: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]
```

### 3.5 写作流程模块 (Writing)

```python
# POST   /api/v1/writing/outline         # 生成大纲
# POST   /api/v1/writing/draft           # 生成草稿
# POST   /api/v1/writing/edit            # 编辑内容
# POST   /api/v1/writing/complete        # 完整写作流程
# POST   /api/v1/writing/continue        # 续写
# POST   /api/v1/writing/expand          # 扩写
# POST   /api/v1/writing/condense        # 缩写
# POST   /api/v1/writing/polish          # 润色
```

**Schema:**
```python
class WritingRequest(BaseModel):
    session_id: str
    task_type: str = "article"
    topic: str
    audience: Optional[str] = None
    goal: Optional[str] = None
    tone: Optional[str] = None
    length: Optional[str] = "medium"
    language: str = "zh"
    style: str = "professional"
    use_rag: bool = False
    use_web: bool = False
    extra_context: Optional[str] = None

class OutlineResponse(BaseModel):
    title: str
    sections: list[Section]
    estimated_length: str

class WritingProgressResponse(BaseModel):
    task_id: str
    stage: str
    progress: float
    message: str
    partial_result: Optional[str] = None
```

### 3.6 知识库模块 (Knowledge)

```python
# GET    /api/v1/knowledge                       # 获取知识库列表
# POST   /api/v1/knowledge                       # 创建知识库
# GET    /api/v1/knowledge/{name}               # 获取知识库详情
# DELETE /api/v1/knowledge/{name}               # 删除知识库
# POST   /api/v1/knowledge/{name}/documents     # 添加文档
# GET    /api/v1/knowledge/{name}/documents     # 获取文档列表
# DELETE /api/v1/knowledge/{name}/documents/{id} # 删除文档
# POST   /api/v1/knowledge/{name}/search        # 搜索知识库
```

**Schema:**
```python
class KnowledgeBaseCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None

class KnowledgeBaseResponse(BaseModel):
    name: str
    description: Optional[str]
    document_count: int
    created_at: datetime

class DocumentUploadRequest(BaseModel):
    files: list[UploadFile]

class SearchRequest(BaseModel):
    query: str
    top_k: int = 5

class SearchResult(BaseModel):
    content: str
    source: str
    relevance_score: float
    metadata: dict
```

### 3.7 SSE 实时推送模块

```python
# GET    /api/v1/sse/connect/{session_id}       # 建立 SSE 连接
# GET    /api/v1/sse/tasks/{task_id}            # 订阅任务进度
```

**消息格式:**
```python
class SSEMessage(BaseModel):
    event: str  # "chat", "progress", "error", "complete", "heartbeat"
    data: dict
    id: Optional[str] = None

class ChatStreamMessage(BaseModel):
    event: str = "chat_stream"
    content: str
    is_end: bool

class TaskProgressMessage(BaseModel):
    event: str = "task_progress"
    task_id: str
    stage: str
    progress: float
    message: str
```

---

## 4. 控制层设计

### 4.1 控制器基类

```python
# api/controllers/base.py

from abc import ABC
from typing import Generic, TypeVar

from fastapi import HTTPException, status

T = TypeVar('T')

class BaseController(ABC, Generic[T]):
    """控制器基类"""

    def __init__(self):
        self.service: T = None

    def handle_error(self, error: Exception, message: str = None) -> None:
        """统一错误处理"""
        if isinstance(error, ValueError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=message or str(error)
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=message or "服务器内部错误"
            )
```

### 4.2 写作控制器

```python
# api/controllers/writing_controller.py

from typing import AsyncGenerator
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse

from services.models import WritingRequest

class WritingController:
    """写作流程控制器"""

    def __init__(self):
        from agents.writer import WriterAgent
        self.agent = WriterAgent()

    async def generate_outline(
        self,
        request: WritingRequest
    ) -> OutlineResponse:
        """生成大纲"""
        # 调用现有 WriterAgent 生成大纲
        result = await self.agent.generate_outline(request)
        return OutlineResponse(**result)

    async def write_draft(
        self,
        request: WritingRequest,
        outline: Outline
    ) -> DraftResponse:
        """生成草稿"""
        result = await self.agent.write_draft(request, outline)
        return DraftResponse(**result)

    async def stream_chat(
        self,
        session_id: str,
        message: str
    ) -> EventSourceResponse:
        """流式对话（SSE）"""
        async def event_generator():
            async for chunk in self.agent.astream_chat(session_id, message):
                yield {
                    "event": "chat_stream",
                    "data": json.dumps({
                        "content": chunk,
                        "is_end": False
                    })
                }
            # 结束标记
            yield {
                "event": "chat_stream",
                "data": json.dumps({
                    "content": "",
                    "is_end": True
                })
            }

        return EventSourceResponse(event_generator())

    async def edit_content(
        self,
        content: str,
        edit_type: str,
        instructions: str
    ) -> EditResponse:
        """编辑内容"""
        result = await self.agent.edit(content, edit_type, instructions)
        return EditResponse(content=result)
```

### 4.3 任务控制器

```python
# api/controllers/task_controller.py

from services.writing_task_service import get_writing_task_service

class TaskController:
    """任务控制器"""

    def __init__(self):
        self.service = get_writing_task_service()

    async def create_task(
        self,
        session_id: str,
        task_type: str,
        topic: str,
        request: dict
    ) -> TaskResponse:
        """创建任务"""
        task = self.service.create_task(
            session_id=session_id,
            task_type=task_type,
            topic=topic,
            request=request
        )
        return TaskResponse.model_validate(task)

    async def start_task(self, task_id: str) -> TaskResponse:
        """开始任务"""
        success = self.service.start_task(task_id)
        if not success:
            raise ValueError("任务启动失败")
        return await self.get_task(task_id)

    async def get_task(self, task_id: str) -> TaskResponse:
        """获取任务"""
        task = self.service.get_task(task_id)
        if not task:
            raise ValueError("任务不存在")
        return TaskResponse.model_validate(task)

    async def stream_task_progress(
        self,
        task_id: str
    ) -> EventSourceResponse:
        """流式推送任务进度"""
        from api.utils.sse_manager import sse_manager

        async def event_generator():
            queue = await sse_manager.subscribe(task_id)
            try:
                while True:
                    message = await queue.get()
                    if message.get("event") == "complete":
                        yield message
                        break
                    yield message
            finally:
                await sse_manager.unsubscribe(task_id, queue)

        return EventSourceResponse(event_generator())
```

---

## 5. SSE 管理器

```python
# api/utils/sse_manager.py

import asyncio
from typing import Dict, List, AsyncQueue

class SSEManager:
    """SSE 连接管理器"""

    def __init__(self):
        self._subscriptions: Dict[str, List[asyncio.Queue]] = {}

    async def subscribe(self, channel: str) -> asyncio.Queue:
        """订阅频道"""
        if channel not in self._subscriptions:
            self._subscriptions[channel] = []
        queue = asyncio.Queue()
        self._subscriptions[channel].append(queue)
        return queue

    async def unsubscribe(self, channel: str, queue: asyncio.Queue):
        """取消订阅"""
        if channel in self._subscriptions:
            if queue in self._subscriptions[channel]:
                self._subscriptions[channel].remove(queue)

    async def publish(self, channel: str, message: dict):
        """发布消息到频道"""
        if channel in self._subscriptions:
            for queue in self._subscriptions[channel]:
                await queue.put(message)

    async def broadcast(self, message: dict):
        """广播消息到所有频道"""
        for channel in self._subscriptions:
            await self.publish(channel, message)

# 全局实例
sse_manager = SSEManager()
```

---

## 6. 依赖注入

```python
# api/dependencies.py

from fastapi import Depends, HTTPException, status

from services.session_service import get_session_service
from services.document_service import get_document_service
from services.writing_task_service import get_writing_task_service

async def get_session_service_dep():
    """获取会话服务"""
    return get_session_service()

async def get_document_service_dep():
    """获取文档服务"""
    return get_document_service()

async def get_task_service_dep():
    """获取任务服务"""
    return get_writing_task_service()

async def validate_session_exists(
    session_id: str,
    session_service = Depends(get_session_service_dep)
):
    """验证会话存在"""
    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"会话 {session_id} 不存在"
        )
    return session
```

---

## 7. 中间件

### 7.1 错误处理中间件

```python
# api/middlewares/error_handler.py

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import logging

logger = logging.getLogger(__name__)

class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """全局错误处理中间件"""

    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except HTTPException as e:
            return JSONResponse(
                status_code=e.status_code,
                content={
                    "success": False,
                    "error": {
                        "code": e.status_code,
                        "message": e.detail
                    }
                }
            )
        except Exception as e:
            logger.error(f"Unhandled error: {e}", exc_info=True)
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "error": {
                        "code": 500,
                        "message": "服务器内部错误"
                    }
                }
            )
```

### 7.2 请求日志中间件

```python
# api/middlewares/logging.py

import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import logging

logger = logging.getLogger(__name__)

class LoggingMiddleware(BaseHTTPMiddleware):
    """请求日志中间件"""

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        logger.info(f"Request: {request.method} {request.url.path}")

        response = await call_next(request)

        process_time = time.time() - start_time
        logger.info(
            f"Response: {request.method} {request.url.path} "
            f"- Status: {response.status_code} - Time: {process_time:.3f}s"
        )

        response.headers["X-Process-Time"] = str(process_time)
        return response
```

### 7.3 CORS 中间件

```python
# api/middlewares/cors.py

from fastapi.middleware.cors import CORSMiddleware

def setup_cors(app):
    """配置 CORS"""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 生产环境应配置具体域名
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
```

---

## 8. 统一响应格式

```python
# api/utils/response.py

from typing import Generic, TypeVar, Optional
from pydantic import BaseModel

T = TypeVar('T')

class ResponseModel(BaseModel, Generic[T]):
    """统一响应模型"""
    success: bool = True
    data: Optional[T] = None
    message: Optional[str] = None
    error: Optional[dict] = None

class PaginationModel(BaseModel, Generic[T]):
    """分页响应模型"""
    total: int
    page: int
    page_size: int
    items: list[T]

def success_response(data: T = None, message: str = None) -> ResponseModel[T]:
    """成功响应"""
    return ResponseModel(
        success=True,
        data=data,
        message=message
    )

def error_response(code: int, message: str, details: dict = None) -> ResponseModel:
    """错误响应"""
    return ResponseModel(
        success=False,
        error={
            "code": code,
            "message": message,
            "details": details
        }
    )
```

---

## 9. 主应用入口

```python
# api/main.py

from fastapi import FastAPI
from contextlib import asynccontextmanager

from api.middlewares.cors import setup_cors
from api.middlewares.error_handler import ErrorHandlerMiddleware
from api.middlewares.logging import LoggingMiddleware
from api.routers import sessions, messages, documents, tasks, knowledge, writing, sse

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    print("Starting DeepWriter API...")
    yield
    # 关闭时执行
    print("Shutting down DeepWriter API...")

app = FastAPI(
    title="DeepWriter API",
    description="AI 写作助手 API",
    version="0.1.0",
    lifespan=lifespan
)

# 配置中间件
setup_cors(app)
app.add_middleware(ErrorHandlerMiddleware)
app.add_middleware(LoggingMiddleware)

# 注册路由
app.include_router(sessions.router, prefix="/api/v1", tags=["sessions"])
app.include_router(messages.router, prefix="/api/v1", tags=["messages"])
app.include_router(documents.router, prefix="/api/v1", tags=["documents"])
app.include_router(tasks.router, prefix="/api/v1", tags=["tasks"])
app.include_router(knowledge.router, prefix="/api/v1", tags=["knowledge"])
app.include_router(writing.router, prefix="/api/v1", tags=["writing"])
app.include_router(sse.router, prefix="/api/v1", tags=["sse"])

@app.get("/")
async def root():
    return {"message": "DeepWriter API", "version": "0.1.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

---

## 10. 实现步骤

### Phase 1: 基础架构 (第 1 天)

**任务 1.1**: 创建 API 目录结构
- [ ] 创建 `api/` 目录及所有子目录
- [ ] 更新 `pyproject.toml` 添加 FastAPI 依赖

**任务 1.2**: 配置 FastAPI 应用
- [ ] 创建 `api/config.py` 配置文件
- [ ] 创建 `api/main.py` 应用入口
- [ ] 配置 CORS 和中间件

**任务 1.3**: 定义基础 Schema
- [ ] 创建 `api/schemas/base.py`
- [ ] 创建 `api/utils/response.py`
- [ ] 创建 `api/utils/exceptions.py`

### Phase 2: 核心模块 (第 2-3 天)

**任务 2.1**: 会话管理 API
- [ ] 创建 `api/schemas/session.py`
- [ ] 创建 `api/controllers/session_controller.py`
- [ ] 创建 `api/routers/sessions.py`

**任务 2.2**: 消息对话 API
- [ ] 创建 `api/schemas/message.py`
- [ ] 创建 `api/routers/messages.py`

**任务 2.3**: 文档管理 API
- [ ] 创建 `api/schemas/document.py`
- [ ] 创建 `api/controllers/document_controller.py`
- [ ] 创建 `api/routers/documents.py`

**任务 2.4**: 任务管理 API
- [ ] 创建 `api/schemas/task.py`
- [ ] 创建 `api/controllers/task_controller.py`
- [ ] 创建 `api/routers/tasks.py`

### Phase 3: 写作流程 API (第 4-5 天)

**任务 3.1**: 写作流程 Schema
- [ ] 创建 `api/schemas/writing.py`
- [ ] 定义所有写作相关请求/响应模型

**任务 3.2**: 写作控制器
- [ ] 创建 `api/controllers/writing_controller.py`
- [ ] 实现大纲生成、草稿写作等方法

**任务 3.3**: 写作路由
- [ ] 创建 `api/routers/writing.py`
- [ ] 实现所有写作相关接口

**任务 3.4**: 知识库路由
- [ ] 创建 `api/schemas/knowledge.py`
- [ ] 创建 `api/routers/knowledge.py`

### Phase 4: SSE 实时通信 (第 6 天)

**任务 4.1**: SSE 管理器
- [ ] 创建 `api/utils/sse_manager.py`
- [ ] 实现订阅/发布机制

**任务 4.2**: SSE 路由
- [ ] 创建 `api/routers/sse.py`
- [ ] 实现 SSE 连接端点

**任务 4.3**: 流式响应集成
- [ ] 集成 LLM 流式输出到 SSE
- [ ] 实现任务进度推送

### Phase 5: 测试与文档 (第 7 天)

**任务 5.1**: API 测试
- [ ] 创建 `tests/test_api/`
- [ ] 编写接口测试用例
- [ ] 使用 pytest + httpx

**任务 5.2**: API 文档
- [ ] 完善接口描述
- [ ] 添加示例数据
- [ ] 生成 OpenAPI 文档

---

## 11. 依赖更新

更新 `pyproject.toml`:

```toml
[project]
dependencies = [
    # ... 现有依赖
    "fastapi>=0.110.0",
    "uvicorn[standard]>=0.27.0",
    "python-multipart>=0.0.9",
    "sse-starlette>=2.0.0",
]

[project.optional-dependencies]
dev = [
    # ... 现有依赖
    "httpx>=0.27.0",
]
```

---

## 12. 启动命令

```bash
# 开发模式
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# 生产模式
uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

---

## 13. API 文档访问

启动后访问:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

---

## 14. 与前端集成建议

### 14.1 前端技术栈建议
- **框架**: React 18 + TypeScript
- **状态管理**: Zustand 或 Redux Toolkit
- **HTTP 客户端**: Axios 或 TanStack Query
- **UI 组件**: Ant Design 或 Chakra UI
- **SSE 客户端**: EventSource API

### 14.2 SSE 客户端示例
```javascript
// 建立 SSE 连接
const eventSource = new EventSource('/api/v1/sse/connect/session-123');

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Received:', data);
};

eventSource.addEventListener('chat_stream', (event) => {
  const data = JSON.parse(event.data);
  appendToChat(data.content);
  if (data.is_end) {
    eventSource.close();
  }
});
```

---

## 15. 验收标准

### 15.1 功能验收
- [ ] 所有 API 端点正常工作
- [ ] 会话 CRUD 完整
- [ ] 消息对话流畅
- [ ] 文档版本管理正常
- [ ] 写作流程可执行
- [ ] SSE 实时推送正常

### 15.2 性能验收
- [ ] API 响应时间 < 200ms (不含 LLM 调用)
- [ ] SSE 消息延迟 < 100ms
- [ ] 支持 100+ 并发 SSE 连接

### 15.3 安全验收
- [ ] 输入验证完整
- [ ] SQL 注入防护
- [ ] XSS 防护
