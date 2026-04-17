"""RAG检索工具模块"""



from abc import ABC, abstractmethod
from typing import Any, Optional

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from services.rag.pipeline import RAGPipeline
from services.rag.types import SearchResult
from services.rag.components.retrievers.dense import DenseRetriever
from services.rag.components.embedders.openai import OpenAIEmbedder
from services.rag.components.indexers.vector import VectorIndexer


class RAGRetrievalInput(BaseModel):
    """RAG检索输入参数"""
    query: str = Field(description="检索查询内容")
    kb_name: str = Field(description="知识库名称")
    top_k: int = Field(default=5, description="返回结果数量", ge=1, le=20)
    score_threshold: float = Field(default=0.0, description="相似度阈值(0-1)", ge=0.0, le=1.0)


class BaseRAGRetrievalTool(BaseTool, ABC):


    name: str = "rag_retrieval"
    description: str = """从知识库中检索相关文档片段。
    适用于需要查询本地知识库、获取文档内容的场景。
    输入应包含查询内容和目标知识库名称。
    """
    args_schema: type[BaseModel] = RAGRetrievalInput

    def __init__(
        self,
        kb_base_dir: Optional[str] = None,
        embedder: Optional[Any] = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self._kb_base_dir = kb_base_dir
        self._embedder = embedder
        self._pipeline: Optional[RAGPipeline] = None

    def _get_pipeline(self) -> RAGPipeline:
        """获取或创建RAG管道

        延迟初始化模式，只在需要时创建管道实例
        """
        if self._pipeline is None:
            self._pipeline = self.create_pipeline()
        return self._pipeline

    @abstractmethod
    def create_pipeline(self) -> RAGPipeline:
        """创建RAG管道实例

        子类必须实现此方法以提供具体的检索流程配置。
        这是扩展点，允许不同的检索策略（密集检索、稀疏检索、混合检索等）

        Returns:
            配置好的RAGPipeline实例
        """
        pass

    def _format_result(self, result: SearchResult) -> str:
        """格式化检索结果

        子类可以重写此方法来自定义输出格式
        """
        if not result.chunks:
            return "未找到相关结果。"

        lines = []
        lines.append(f"【检索结果】共找到 {len(result.chunks)} 个相关片段")
        lines.append(f"检索耗时: {result.search_time_ms:.1f}ms")
        lines.append("")

        for i, source in enumerate(result.sources, 1):
            lines.append(f"{i}. {source.title} (相似度: {source.score:.4f})")
            if source.source:
                lines.append(f"   来源: {source.source}")
            content = source.content[:300] + "..." if len(source.content) > 300 else source.content
            lines.append(f"   内容: {content}")
            lines.append("")

        return "\n".join(lines)

    def _run(
        self,
        query: str,
        kb_name: str,
        top_k: int = 5,
        score_threshold: float = 0.0
    ) -> str:
        """同步执行检索

        Args:
            query: 检索查询
            kb_name: 知识库名称
            top_k: 返回结果数量
            score_threshold: 相似度阈值

        Returns:
            格式化的检索结果字符串
        """
        import asyncio

        try:
            try:
                loop = asyncio.get_running_loop()
                # 如果在异步环境中，使用 nest_asyncio
                import nest_asyncio
                nest_asyncio.apply()
                result = loop.run_until_complete(
                    self._aretrieve(query, kb_name, top_k, score_threshold)
                )
            except RuntimeError:
                # 没有运行中的事件循环，创建新的
                result = asyncio.run(
                    self._aretrieve(query, kb_name, top_k, score_threshold)
                )
            return self._format_result(result)
        except Exception as e:
            return f"检索失败: {str(e)}"

    async def _arun(
        self,
        query: str,
        kb_name: str,
        top_k: int = 5,
        score_threshold: float = 0.0
    ) -> str:
        """异步执行检索"""
        try:
            result = await self._aretrieve(query, kb_name, top_k, score_threshold)
            return self._format_result(result)
        except Exception as e:
            return f"检索失败: {str(e)}"

    async def _aretrieve(
        self,
        query: str,
        kb_name: str,
        top_k: int,
        score_threshold: float
    ) -> SearchResult:
        """执行实际检索操作

        Args:
            query: 检索查询
            kb_name: 知识库名称
            top_k: 返回结果数量
            score_threshold: 相似度阈值

        Returns:
            SearchResult对象
        """
        pipeline = self._get_pipeline()

        # 配置检索器参数
        retriever_kwargs = {
            "top_k": top_k,
            "score_threshold": score_threshold
        }

        return await pipeline.search(query, kb_name, **retriever_kwargs)


class DenseRAGRetrievalTool(BaseRAGRetrievalTool):
    """密集向量检索工具

    使用向量相似度进行检索的默认实现。
    基于DenseRetriever，使用OpenAI嵌入模型和ChromaDB向量数据库。
    """

    name: str = "dense_rag_retrieval"
    description: str = """使用密集向量相似度从知识库中检索相关文档片段。
    适用于语义搜索、概念匹配等场景。
    输入应包含查询内容和目标知识库名称。
    返回按相似度排序的相关文档片段。
    """

    def create_pipeline(self) -> RAGPipeline:
        """创建密集向量检索管道

        配置：
        - 嵌入器：OpenAIEmbedder
        - 检索器：DenseRetriever
        """
        embedder = self._embedder or OpenAIEmbedder()

        pipeline = RAGPipeline(
            name="dense_retrieval",
            kb_base_dir=self._kb_base_dir
        )

        # 配置检索器
        retriever = DenseRetriever(
            kb_base_dir=self._kb_base_dir,
            embedder=embedder,
            top_k=5
        )

        pipeline.retriever(retriever)
        return pipeline


class RAGRetrievalToolFactory:
    """RAG检索工具工厂

    提供统一的方式来创建不同类型的RAG检索工具。
    便于管理和扩展新的检索策略。
    """

    _registry: dict[str, type[BaseRAGRetrievalTool]] = {
        "dense": DenseRAGRetrievalTool,
    }

    @classmethod
    def register(
        cls,
        name: str,
        tool_class: type[BaseRAGRetrievalTool]
    ) -> None:
        """注册新的检索工具类型

        扩展点：允许注册自定义检索工具而无需修改现有代码

        Args:
            name: 工具类型名称
            tool_class: 工具类，必须是BaseRAGRetrievalTool的子类
        """
        if not issubclass(tool_class, BaseRAGRetrievalTool):
            raise ValueError(f"工具类必须继承自BaseRAGRetrievalTool")
        cls._registry[name] = tool_class

    @classmethod
    def create(
        cls,
        tool_type: str = "dense",
        **kwargs
    ) -> BaseRAGRetrievalTool:
        """创建检索工具实例

        Args:
            tool_type: 工具类型名称
            **kwargs: 传递给工具构造函数的参数

        Returns:
            BaseRAGRetrievalTool实例

        Raises:
            ValueError: 如果工具类型未注册
        """
        if tool_type not in cls._registry:
            available = ", ".join(cls._registry.keys())
            raise ValueError(f"未知的工具类型: {tool_type}. 可用类型: {available}")

        tool_class = cls._registry[tool_type]
        return tool_class(**kwargs)

    @classmethod
    def list_available(cls) -> list[str]:
        """获取所有可用的工具类型"""
        return list(cls._registry.keys())


def get_rag_retrieval_tool(
    tool_type: str = "dense",
    kb_base_dir: Optional[str] = None,
    embedder: Optional[Any] = None
) -> BaseRAGRetrievalTool:
    """获取RAG检索工具实例的便捷函数

    Args:
        tool_type: 工具类型，默认为"dense"
        kb_base_dir: 知识库基础目录
        embedder: 自定义嵌入器实例

    Returns:
        BaseRAGRetrievalTool实例

    Example:
        >>> tool = get_rag_retrieval_tool("dense")
        >>> result = tool.invoke({"query": "什么是AI", "kb_name": "tech_docs"})
    """
    return RAGRetrievalToolFactory.create(
        tool_type=tool_type,
        kb_base_dir=kb_base_dir,
        embedder=embedder
    )
