from fastapi.middleware.cors import CORSMiddleware


def setup_cors(app):
    """配置 CORS"""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
