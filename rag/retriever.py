from abc import ABC, abstractmethod
from typing import Optional

from langchain_core.documents import Document as LCDocument
from pydantic import BaseModel, Field


class Document(BaseModel):
    content: str
    metadata: dict = Field(default_factory=dict)
    id: Optional[str] = None


class RetrievalResult(BaseModel):
    documents: list[Document]
    scores: list[float] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)


class BaseRetriever(ABC):
    @abstractmethod
    async def add_documents(self, documents: list[Document]) -> list[str]:
        pass

    @abstractmethod
    async def retrieve(self, query: str, k: int = 4) -> RetrievalResult:
        pass

    @abstractmethod
    async def delete(self, ids: list[str]) -> bool:
        pass


class VectorStoreRetriever(BaseRetriever):
    def __init__(self, vectorstore, k: int = 4):
        self.vectorstore = vectorstore
        self.k = k

    async def add_documents(self, documents: list[Document]) -> list[str]:
        lc_docs = [
            LCDocument(page_content=doc.content, metadata=doc.metadata)
            for doc in documents
        ]
        ids = await self.vectorstore.aadd_documents(lc_docs)
        return ids

    async def retrieve(self, query: str, k: Optional[int] = None) -> RetrievalResult:
        k = k or self.k
        results = await self.vectorstore.asimilarity_search_with_score(query, k=k)

        documents = []
        scores = []
        for doc, score in results:
            documents.append(
                Document(content=doc.page_content, metadata=doc.metadata)
            )
            scores.append(score)

        return RetrievalResult(documents=documents, scores=scores)

    async def delete(self, ids: list[str]) -> bool:
        try:
            await self.vectorstore.adelete(ids=ids)
            return True
        except Exception:
            return False
