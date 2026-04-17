"""
Vector Indexer
==============

Indexer using vector database (ChromaDB).
"""

import json
import os
import shutil
from pathlib import Path
from typing import List, Optional, Dict, Any

import numpy as np

from services.rag.components.indexers.base import BaseIndexer
from services.rag.types import Document, Chunk


class VectorIndexer(BaseIndexer):
    """
    Vector indexer using ChromaDB.

    Stores document chunks with their embeddings for similarity search.
    """

    name: str = "vector_indexer"

    def __init__(self, kb_base_dir: Optional[str] = None):
        super().__init__(kb_base_dir)
        self._chroma_client = None
        self._embedding_function = None

    def _get_chroma_client(self):
        """Lazy import and initialize ChromaDB client."""
        if self._chroma_client is None:
            try:
                import chromadb
                from chromadb.config import Settings as ChromaSettings

                # 使用配置中的持久化目录
                try:
                    from config.settings import Settings
                    settings = Settings()  # 每次都创建新实例，避免缓存问题
                    persist_dir = settings.rag_persist_directory
                except Exception:
                    # 回退到默认路径
                    persist_dir = os.path.join(self.kb_base_dir, "chroma")

                # 确保路径是绝对路径
                if not os.path.isabs(persist_dir):
                    from pathlib import Path
                    project_root = Path(__file__).resolve().parent.parent.parent.parent.parent
                    persist_dir = os.path.join(str(project_root), persist_dir)

                os.makedirs(persist_dir, exist_ok=True)
                print(f"[ChromaDB] 使用持久化目录: {persist_dir}")

                # 使用 PersistentClient 进行持久化存储
                self._chroma_client = chromadb.PersistentClient(
                    path=persist_dir,
                    settings=ChromaSettings(
                        anonymized_telemetry=False,
                    )
                )
            except ImportError:
                raise ImportError(
                    "ChromaDB is required for vector indexing. "
                    "Install with: pip install chromadb"
                )
        return self._chroma_client

    def _get_collection_name(self, kb_name: str) -> str:
        """Get sanitized collection name."""
        # Chroma collection names must be alphanumeric with underscores
        import re
        sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', kb_name)
        return sanitized[:63]  # Chroma limit

    async def index(self, kb_name: str, documents: List[Document], **kwargs) -> bool:
        """
        Index documents into a knowledge base.

        Args:
            kb_name: Knowledge base name
            documents: List of documents to index
            **kwargs: Additional options

        Returns:
            True if successful
        """
        self.logger.info(f"Indexing {len(documents)} documents into KB '{kb_name}'")

        try:
            client = self._get_chroma_client()
            collection_name = self._get_collection_name(kb_name)

            # Delete existing collection if it exists
            try:
                client.delete_collection(collection_name)
                self.logger.info(f"Deleted existing collection: {collection_name}")
            except Exception:
                pass

            # Create new collection
            collection = client.create_collection(
                name=collection_name,
                metadata={"kb_name": kb_name, "document_count": len(documents)},
            )

            # Prepare data for batch insertion
            all_ids = []
            all_embeddings = []
            all_documents = []
            all_metadatas = []

            chunk_id = 0
            for doc in documents:
                for chunk in doc.chunks:
                    if chunk.embedding is None:
                        self.logger.warning(f"Chunk {chunk_id} has no embedding, skipping")
                        continue

                    all_ids.append(f"chunk_{chunk_id}")
                    all_embeddings.append(chunk.embedding)
                    all_documents.append(chunk.content)
                    all_metadatas.append({
                        "file_path": doc.file_path,
                        "file_name": doc.file_name,
                        "chunk_type": chunk.chunk_type,
                        "chunk_index": chunk.index,
                        **chunk.metadata,
                    })
                    chunk_id += 1

            if not all_ids:
                self.logger.warning("No chunks to index")
                return False

            # Batch add to collection
            batch_size = 100
            for i in range(0, len(all_ids), batch_size):
                end_idx = min(i + batch_size, len(all_ids))
                collection.add(
                    ids=all_ids[i:end_idx],
                    embeddings=all_embeddings[i:end_idx],
                    documents=all_documents[i:end_idx],
                    metadatas=all_metadatas[i:end_idx],
                )
                self.logger.debug(f"Indexed batch {i//batch_size + 1}: {end_idx - i} chunks")

            # Save metadata
            self._save_kb_metadata(kb_name, documents)

            self.logger.info(f"Successfully indexed {len(all_ids)} chunks into KB '{kb_name}'")
            return True

        except Exception as e:
            self.logger.error(f"Failed to index documents: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return False

    async def add_documents(self, kb_name: str, documents: List[Document], **kwargs) -> bool:
        """
        Add documents to an existing knowledge base.

        Args:
            kb_name: Knowledge base name
            documents: List of documents to add
            **kwargs: Additional options

        Returns:
            True if successful
        """
        self.logger.info(f"Adding {len(documents)} documents to KB '{kb_name}'")

        try:
            client = self._get_chroma_client()
            collection_name = self._get_collection_name(kb_name)

            # Get existing collection
            try:
                collection = client.get_collection(collection_name)
            except Exception:
                self.logger.warning(f"Collection '{collection_name}' not found, creating new")
                return await self.index(kb_name, documents, **kwargs)

            # Get current count for ID generation
            existing_count = collection.count()

            # Prepare data for insertion
            all_ids = []
            all_embeddings = []
            all_documents = []
            all_metadatas = []

            chunk_id = existing_count
            for doc in documents:
                for chunk in doc.chunks:
                    if chunk.embedding is None:
                        continue

                    all_ids.append(f"chunk_{chunk_id}")
                    all_embeddings.append(chunk.embedding)
                    all_documents.append(chunk.content)
                    all_metadatas.append({
                        "file_path": doc.file_path,
                        "file_name": doc.file_name,
                        "chunk_type": chunk.chunk_type,
                        "chunk_index": chunk.index,
                        **chunk.metadata,
                    })
                    chunk_id += 1

            if not all_ids:
                return False

            # Batch add
            batch_size = 100
            for i in range(0, len(all_ids), batch_size):
                end_idx = min(i + batch_size, len(all_ids))
                collection.add(
                    ids=all_ids[i:end_idx],
                    embeddings=all_embeddings[i:end_idx],
                    documents=all_documents[i:end_idx],
                    metadatas=all_metadatas[i:end_idx],
                )

            # Update metadata
            existing_docs = self._load_kb_metadata(kb_name) or []
            existing_docs.extend([doc.to_dict() for doc in documents])
            self._save_kb_metadata(kb_name, documents, existing_docs)

            self.logger.info(f"Successfully added {len(all_ids)} chunks to KB '{kb_name}'")
            return True

        except Exception as e:
            self.logger.error(f"Failed to add documents: {e}")
            return False

    async def delete(self, kb_name: str, **kwargs) -> bool:
        """
        Delete a knowledge base.

        Args:
            kb_name: Knowledge base name
            **kwargs: Additional options

        Returns:
            True if successful
        """
        self.logger.info(f"Deleting KB '{kb_name}'")

        try:
            # Delete Chroma collection
            client = self._get_chroma_client()
            collection_name = self._get_collection_name(kb_name)

            try:
                client.delete_collection(collection_name)
                self.logger.info(f"Deleted Chroma collection: {collection_name}")
            except Exception as e:
                self.logger.warning(f"Collection not found or error: {e}")

            # Delete metadata file
            kb_dir = Path(self.kb_base_dir) / kb_name
            if kb_dir.exists():
                shutil.rmtree(kb_dir)
                self.logger.info(f"Deleted KB directory: {kb_dir}")

            return True

        except Exception as e:
            self.logger.error(f"Failed to delete KB: {e}")
            return False

    def _save_kb_metadata(self, kb_name: str, documents: List[Document], existing: List[Dict] = None) -> None:
        """Save knowledge base metadata."""
        kb_dir = Path(self.kb_base_dir) / kb_name
        kb_dir.mkdir(parents=True, exist_ok=True)

        metadata = {
            "kb_name": kb_name,
            "document_count": len(documents) + (len(existing) if existing else 0),
            "documents": existing or [doc.to_dict() for doc in documents],
        }

        metadata_path = kb_dir / "metadata.json"
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

    def _load_kb_metadata(self, kb_name: str) -> Optional[List[Dict]]:
        """Load knowledge base metadata."""
        metadata_path = Path(self.kb_base_dir) / kb_name / "metadata.json"
        if metadata_path.exists():
            with open(metadata_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("documents", [])
        return None

    def get_collection(self, kb_name: str):
        """Get Chroma collection for a knowledge base."""
        client = self._get_chroma_client()
        collection_name = self._get_collection_name(kb_name)
        return client.get_collection(collection_name)
