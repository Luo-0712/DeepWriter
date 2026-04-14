"""
文档服务层

提供文档管理的高级业务逻辑。
"""

from typing import Optional

from db.database import Database, get_db
from db.models import Document as DocumentModel
from db.models import DocumentVersion as DocumentVersionModel
from db.repositories import DocumentRepository, DocumentVersionRepository


class DocumentService:
    """
    文档服务

    管理文档的创建、版本控制和内容管理。
    """

    def __init__(self, db: Optional[Database] = None):
        self.db = db or get_db()
        self.document_repo = DocumentRepository(self.db)
        self.version_repo = DocumentVersionRepository(self.db)

    def create_document(
        self,
        session_id: str,
        title: str,
        content: str = "",
        doc_type: str = "article",
        metadata: Optional[dict] = None,
    ) -> DocumentModel:
        """
        创建新文档

        Args:
            session_id: 会话 ID
            title: 文档标题
            content: 文档内容
            doc_type: 文档类型
            metadata: 元数据

        Returns:
            DocumentModel: 创建的文档
        """
        document = DocumentModel(
            session_id=session_id,
            title=title,
            content=content,
            doc_type=doc_type,
            metadata=metadata or {},
        )
        document = self.document_repo.create(document)

        # 创建初始版本
        self._create_version(document, "初始版本")

        return document

    def get_document(self, document_id: str) -> Optional[DocumentModel]:
        """
        获取文档

        Args:
            document_id: 文档 ID

        Returns:
            Optional[DocumentModel]: 文档对象
        """
        return self.document_repo.get_by_id(document_id)

    def get_session_documents(self, session_id: str) -> list[DocumentModel]:
        """
        获取会话的所有文档

        Args:
            session_id: 会话 ID

        Returns:
            list[DocumentModel]: 文档列表
        """
        return self.document_repo.get_by_session_id(session_id)

    def update_document(
        self,
        document_id: str,
        title: Optional[str] = None,
        content: Optional[str] = None,
        create_version: bool = False,
        change_summary: Optional[str] = None,
    ) -> Optional[DocumentModel]:
        """
        更新文档

        Args:
            document_id: 文档 ID
            title: 新标题
            content: 新内容
            create_version: 是否创建版本
            change_summary: 变更摘要

        Returns:
            Optional[DocumentModel]: 更新后的文档
        """
        document = self.document_repo.get_by_id(document_id)
        if not document:
            return None

        # 如果需要创建版本，先保存当前版本
        if create_version:
            self._create_version(document, change_summary or "自动保存")

        if title is not None:
            document.title = title
        if content is not None:
            document.content = content

        return self.document_repo.update(document)

    def update_content(
        self, document_id: str, content: str, create_version: bool = False
    ) -> bool:
        """
        更新文档内容

        Args:
            document_id: 文档 ID
            content: 新内容
            create_version: 是否创建版本

        Returns:
            bool: 是否成功
        """
        document = self.document_repo.get_by_id(document_id)
        if not document:
            return False

        if create_version:
            self._create_version(document, "内容更新")

        return self.document_repo.update_content(document_id, content)

    def publish_document(self, document_id: str) -> bool:
        """
        发布文档

        Args:
            document_id: 文档 ID

        Returns:
            bool: 是否成功
        """
        return self.document_repo.update_status(document_id, "published")

    def archive_document(self, document_id: str) -> bool:
        """
        归档文档

        Args:
            document_id: 文档 ID

        Returns:
            bool: 是否成功
        """
        return self.document_repo.update_status(document_id, "archived")

    def delete_document(self, document_id: str) -> bool:
        """
        删除文档及其所有版本

        Args:
            document_id: 文档 ID

        Returns:
            bool: 是否成功
        """
        # 先删除版本
        self.version_repo.delete_by_document_id(document_id)
        # 再删除文档
        return self.document_repo.delete(document_id)

    def _create_version(self, document: DocumentModel, change_summary: str) -> DocumentVersionModel:
        """
        创建文档版本

        Args:
            document: 文档对象
            change_summary: 变更摘要

        Returns:
            DocumentVersionModel: 创建的版本
        """
        version_number = self.version_repo.get_next_version_number(document.id)
        version = DocumentVersionModel(
            document_id=document.id,
            version=version_number,
            title=document.title,
            content=document.content,
            change_summary=change_summary,
        )
        return self.version_repo.create(version)

    def create_version(
        self, document_id: str, change_summary: str
    ) -> Optional[DocumentVersionModel]:
        """
        手动创建文档版本

        Args:
            document_id: 文档 ID
            change_summary: 变更摘要

        Returns:
            Optional[DocumentVersionModel]: 创建的版本
        """
        document = self.document_repo.get_by_id(document_id)
        if not document:
            return None
        return self._create_version(document, change_summary)

    def get_document_versions(self, document_id: str) -> list[DocumentVersionModel]:
        """
        获取文档的所有版本

        Args:
            document_id: 文档 ID

        Returns:
            list[DocumentVersionModel]: 版本列表
        """
        return self.version_repo.get_by_document_id(document_id)

    def get_latest_version(self, document_id: str) -> Optional[DocumentVersionModel]:
        """
        获取文档的最新版本

        Args:
            document_id: 文档 ID

        Returns:
            Optional[DocumentVersionModel]: 最新版本
        """
        return self.version_repo.get_latest_by_document_id(document_id)

    def restore_version(self, document_id: str, version_number: int) -> Optional[DocumentModel]:
        """
        恢复到指定版本

        Args:
            document_id: 文档 ID
            version_number: 版本号

        Returns:
            Optional[DocumentModel]: 恢复后的文档
        """
        versions = self.version_repo.get_by_document_id(document_id)
        target_version = None
        for v in versions:
            if v.version == version_number:
                target_version = v
                break

        if not target_version:
            return None

        # 先创建当前版本的备份
        document = self.document_repo.get_by_id(document_id)
        if document:
            self._create_version(document, f"恢复到版本 {version_number} 前的备份")

            # 恢复内容
            document.title = target_version.title
            document.content = target_version.content
            return self.document_repo.update(document)

        return None


# 全局服务实例
_document_service: Optional[DocumentService] = None


def get_document_service(db: Optional[Database] = None) -> DocumentService:
    """获取全局 DocumentService 实例"""
    global _document_service
    if _document_service is None:
        _document_service = DocumentService(db)
    return _document_service
