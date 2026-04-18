from fastapi import FastAPI
from contextlib import asynccontextmanager

from api.middlewares.cors import setup_cors
from api.middlewares.error_handler import ErrorHandlerMiddleware
from api.routers import sessions, messages, documents, tasks, knowledge, writing, sse
from db.database import get_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    print("Starting DeepWriter API...")
    
    # 初始化数据库表
    print("Initializing database...")
    db = get_db()
    db.init_tables()
    print(f"Database initialized: {db.db_path}")
    
    yield
    print("Shutting down DeepWriter API...")


app = FastAPI(
    title="DeepWriter API",
    description="AI 写作助手 API",
    version="0.1.0",
    lifespan=lifespan,
)

# 配置中间件
setup_cors(app)
app.add_middleware(ErrorHandlerMiddleware)

# 注册路由
app.include_router(sessions.router, prefix="/api/v1")
app.include_router(messages.router, prefix="/api/v1")
app.include_router(documents.router, prefix="/api/v1")
app.include_router(tasks.router, prefix="/api/v1")
app.include_router(knowledge.router, prefix="/api/v1")
app.include_router(writing.router, prefix="/api/v1")
app.include_router(sse.router, prefix="/api/v1")


@app.get("/")
async def root():
    return {"message": "DeepWriter API", "version": "0.1.0"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
