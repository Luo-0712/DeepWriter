from typing import Optional

from langchain_core.vectorstores import VectorStore
from langchain_community.vectorstores import Chroma, FAISS

from config.settings import Settings, get_settings
from rag.embeddings import create_embeddings


def create_vectorstore(
    store_type: Optional[str] = None,
    settings: Optional[Settings] = None,
) -> VectorStore:
    settings = settings or get_settings()
    store_type = store_type or settings.rag_vector_store
    embeddings = create_embeddings(settings)

    if store_type == "chroma":
        return Chroma(
            embedding_function=embeddings,
            persist_directory=settings.rag_persist_directory,
        )
    elif store_type == "faiss":
        return FAISS(
            embedding_function=embeddings,
        )
    else:
        raise ValueError(f"Unsupported vector store type: {store_type}")
