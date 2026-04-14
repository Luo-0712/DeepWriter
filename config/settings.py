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


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    project_name: str = "DeepWriter"
    debug: bool = False

    llm_provider: LLMProvider = LLMProvider.ZHIPU
    llm_model_name: str = "glm-4.6v"
    llm_temperature: float = 1.0
    llm_max_tokens: int = 65535

    openai_api_key: Optional[str] = None
    openai_api_base: Optional[str] = None

    anthropic_api_key: Optional[str] = None

    azure_openai_api_key: Optional[str] = None
    azure_openai_endpoint: Optional[str] = None
    azure_openai_deployment_name: Optional[str] = None
    azure_openai_api_version: str = "2024-02-15-preview"

    deepseek_api_key: Optional[str] = None
    deepseek_api_base: str = "https://api.deepseek.com/v1"

    zhipu_api_key: Optional[str] = "f95a2a9ed958478cbe07bf0e90c0a5c6.xnD1B95o5rWq1cT5"
    zhipu_api_base: str = "https://open.bigmodel.cn/api/paas/v4"

    qwen_api_key: Optional[str] = None
    qwen_api_base: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"

    rag_embedding_model: str = "text-embedding-3-small"
    rag_vector_store: str = "chroma"
    rag_persist_directory: str = "./data/chroma"
    rag_chunk_size: int = 1000
    rag_chunk_overlap: int = 200

    agent_max_iterations: int = 10
    agent_verbose: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()
