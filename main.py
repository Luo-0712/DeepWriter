import uvicorn
from api.main import app


def main():
    """启动 DeepWriter API 服务"""
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
