from typing import Optional

from langchain_core.embeddings import Embeddings
from langchain_openai import OpenAIEmbeddings

from config.settings import Settings, get_settings


def create_embeddings(settings: Optional[Settings] = None) -> Embeddings:
    settings = settings or get_settings()

    return OpenAIEmbeddings(
        model=settings.rag_embedding_model,
        api_key=settings.openai_api_key,
        base_url=settings.openai_api_base,
    )
