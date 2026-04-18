from enum import Enum
from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMProvider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    AZURE_OPENAI = "azure_openai"
    DEEPSEEK = "deepseek"
    ZHIPU = "zhipu"
    QWEN = "qwen"
    CUSTOM = "custom"


class DatabaseProvider(str, Enum):
    SQLITE = "sqlite"
    POSTGRESQL = "postgresql"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    project_name: str = "DeepWriter"
    debug: bool = False

    database_provider: DatabaseProvider = DatabaseProvider.SQLITE
    database_url: Optional[str] = None

    postgresql_host: str = "localhost"
    postgresql_port: int = 5432
    postgresql_user: str = "postgres"
    postgresql_password: str = "123456"
    postgresql_db: str = "deepwriter"

    llm_provider: LLMProvider = LLMProvider.ZHIPU
    llm_model_name: str = "glm-5.1"
    # llm_model_name: str = "qwen3.6-plus"
    llm_temperature: float = 1.0
    llm_max_tokens: int = 65535

    openai_api_key: Optional[str] = "sk-Cb8eVCKm43JfbNOjABIi9w"
    openai_api_base: Optional[str] = "https://xplt.sdu.edu.cn:4000"

    anthropic_api_key: Optional[str] = None

    azure_openai_api_key: Optional[str] = None
    azure_openai_endpoint: Optional[str] = None
    azure_openai_deployment_name: Optional[str] = None
    azure_openai_api_version: str = "2024-02-15-preview"

    deepseek_api_key: Optional[str] = None
    deepseek_api_base: str = "https://api.deepseek.com/v1"

    zhipu_api_key: Optional[str] = "b2f632d3777d4547b2e9a79a578e19cd.GyeVuO1bqhj9IFZw"
    zhipu_api_base: str = "https://open.bigmodel.cn/api/paas/v4"

    qwen_api_key: Optional[str] = "sk-6301269627534fc8984172bb65330076"
    qwen_api_base: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"

    tavily_api_key: Optional[str] = "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"

    # RAG Configuration
    rag_embedding_model: str = "text-embedding-v1"
    rag_embedding_provider: str = "qwen"  # qwen, openai
    rag_embedding_dim: int = 1024
    rag_vector_store: str = "chroma"
    rag_persist_directory: str = "./data/chroma"
    rag_kb_base_dir: str = "./data/knowledge_bases"
    rag_chunk_size: int = 512
    rag_chunk_overlap: int = 50
    rag_top_k: int = 5

    agent_max_iterations: int = 10
    agent_verbose: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()
