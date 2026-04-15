# DeepWriter RAG 改进计划

## 概述

本计划参考 DeepTutor 的 RAG 实现，为 DeepWriter 设计一套完整的 RAG 增强方案。DeepTutor 的 RAG 系统采用组件化架构，支持灵活的 Pipeline 组合，使用 LlamaIndex 作为核心检索引擎。

---

## 1. 现状分析

### 1.1 DeepWriter 现有 RAG 结构

```
rag/
├── __init__.py
├── embeddings.py      # OpenAI Embeddings 封装
├── retriever.py       # BaseRetriever + VectorStoreRetriever
└── vectorstore.py     # Chroma/FAISS 工厂
```

**当前特点：**
- 使用 LangChain 的 Embeddings 和 VectorStore 抽象
- 支持 Chroma 和 FAISS 两种向量存储
- 简单的文档检索接口

### 1.2 DeepTutor RAG 架构亮点

```
services/rag/
├── __init__.py
├── types.py           # Document, Chunk, SearchResult 数据模型
├── pipeline.py        # 可组合的 RAG Pipeline（流式 API）
├── factory.py         # Pipeline 工厂 + 缓存机制
├── service.py         # RAGService 统一入口
└── components/        # 组件化架构
    ├── base.py        # Component 协议基类
    ├── routing.py     # 文件类型路由（PDF/文本分类）
    ├── parsers/       # 文档解析器
    │   ├── base.py
    │   ├── pdf.py
    │   ├── text.py
    │   └── markdown.py
    ├── chunkers/      # 文本分块器
    │   ├── base.py
    │   ├── fixed.py
    │   ├── semantic.py
    │   └── numbered_item.py
    ├── embedders/     # 嵌入模型
    │   ├── base.py
    │   └── openai.py
    ├── indexers/      # 索引器
    │   ├── base.py
    │   └── vector.py
    └── retrievers/    # 检索器
        ├── base.py
        └── dense.py
```

**核心优势：**
1. **组件化设计**：每个环节（解析、分块、嵌入、索引、检索）都是独立组件
2. **流式 API**：支持链式调用构建 Pipeline
3. **文件路由**：自动分类 PDF/文本文件，采用不同处理策略
4. **LlamaIndex 集成**：使用官方 llama-index 库，支持高级检索功能
5. **统一服务层**：RAGService 封装所有操作，对外提供简洁接口

---

## 2. 改进目标

### 2.1 短期目标（Phase 1）

1. **增强文档处理能力**
   - 支持 PDF 解析（PyMuPDF）
   - 支持 Markdown 结构化解析
   - 自动文件类型检测和路由

2. **改进分块策略**
   - 实现固定大小分块
   - 实现语义分块（按段落/标题）
   - 支持代码块、列表等特殊处理

3. **完善数据模型**
   - 定义 Document、Chunk、SearchResult 类型
   - 支持元数据（来源、页码、标题等）
   - 支持引用信息追踪

### 2.2 中期目标（Phase 2）

1. **引入 LlamaIndex**
   - 替换现有简单封装
   - 使用 VectorStoreIndex 进行高级索引
   - 支持增量文档添加

2. **增强检索能力**
   - 支持混合检索（向量 + 关键词）
   - 支持重排序（Reranking）
   - 支持多知识库管理

3. **Pipeline 化改造**
   - 实现可组合的 RAG Pipeline
   - 支持自定义处理流程
   - 支持进度回调

### 2.3 长期目标（Phase 3）

1. **智能检索**
   - 查询重写/扩展
   - 多查询检索（Multi-query）
   - 结果聚合与摘要

2. **引用与溯源**
   - 自动生成引用
   - 溯源到具体文档位置
   - 支持引用格式输出

---

## 3. 详细实施计划

### Phase 1: 基础增强（预计 3-5 天）

#### 3.1.1 重构数据模型

**新文件：`rag/types.py`**

```python
@dataclass
class Chunk:
    """文档分块"""
    content: str
    chunk_type: str = "text"  # text, code, heading, list...
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[List[float]] = None
    index: int = 0  # 在文档中的顺序

@dataclass
class Document:
    """解析后的文档"""
    content: str
    file_path: str = ""
    file_name: str = ""
    file_type: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    chunks: List[Chunk] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class SearchResult:
    """搜索结果"""
    query: str
    content: str  # 聚合后的内容
    chunks: List[Chunk]  # 匹配的原始块
    sources: List[Dict[str, Any]]  # 来源信息
    total_chunks: int
    search_time_ms: float
```

#### 3.1.2 文件类型路由

**新文件：`rag/routing.py`**

参考 DeepTutor 实现：
- 自动识别 PDF、Markdown、文本、代码文件
- 分类处理：PDF 用解析器，文本直接读取
- 支持编码自动检测（UTF-8、GBK 等）

#### 3.1.3 文档解析器

**新目录：`rag/parsers/`**

| 解析器 | 用途 | 依赖 |
|--------|------|------|
| `pdf_parser.py` | PDF 文本提取 | PyMuPDF (fitz) |
| `markdown_parser.py` | Markdown 结构化解析 | markdown-it-py |
| `text_parser.py` | 纯文本解析 | 内置 |
| `code_parser.py` | 代码文件解析 | 内置 |

#### 3.1.4 分块器

**新目录：`rag/chunkers/`**

| 分块器 | 策略 | 适用场景 |
|--------|------|----------|
| `fixed_chunker.py` | 固定大小 + 重叠 | 通用文本 |
| `semantic_chunker.py` | 按段落/标题分割 | 文章、文档 |
| `code_chunker.py` | 保留函数/类完整 | 代码文件 |

#### 3.1.5 增强现有模块

**修改：`rag/embeddings.py`**
- 添加批量嵌入支持
- 添加进度回调
- 支持更多嵌入模型（OpenAI、本地模型）

**修改：`rag/vectorstore.py`**
- 统一接口，支持多种后端
- 添加集合/知识库管理
- 支持元数据过滤

### Phase 2: LlamaIndex 集成（预计 5-7 天）

#### 3.2.1 LlamaIndex Pipeline

**新文件：`rag/pipelines/llamaindex.py`**

核心功能：
- 使用 `VectorStoreIndex` 进行索引
- 使用 `SentenceSplitter` 进行分块
- 自定义 Embedding 适配器
- 支持增量文档添加

#### 3.2.2 Pipeline 工厂

**新文件：`rag/factory.py`**

```python
def get_pipeline(name: str = "llamaindex", **kwargs) -> RAGPipeline:
    """获取 RAG Pipeline 实例"""
    
def register_pipeline(name: str, factory: Callable) -> None:
    """注册自定义 Pipeline"""
```

#### 3.2.3 统一服务层

**新文件：`rag/service.py`**

```python
class RAGService:
    """RAG 统一服务入口"""
    
    async def initialize_kb(self, kb_name: str, file_paths: List[str]) -> bool:
        """初始化知识库"""
        
    async def search(self, query: str, kb_name: str, **kwargs) -> SearchResult:
        """检索知识库"""
        
    async def add_documents(self, kb_name: str, file_paths: List[str]) -> bool:
        """增量添加文档"""
        
    async def delete_kb(self, kb_name: str) -> bool:
        """删除知识库"""
```

### Phase 3: 高级功能（预计 7-10 天）

#### 3.3.1 智能检索

**新文件：`rag/retrievers/smart.py`**

```python
class SmartRetriever:
    """智能检索器"""
    
    async def retrieve(
        self,
        query: str,
        kb_name: str,
        query_expansion: bool = True,
        rerank: bool = True,
        top_k: int = 5
    ) -> SearchResult:
        # 1. 查询扩展（生成多个相关查询）
        # 2. 并行检索
        # 3. 结果去重和重排序
        # 4. 结果聚合
```

#### 3.3.2 引用与溯源

**新文件：`rag/citation.py`**

```python
class CitationManager:
    """引用管理器"""
    
    def generate_citations(self, chunks: List[Chunk]) -> List[Citation]:
        """为检索结果生成引用"""
        
    def format_references(self, citations: List[Citation], style: str = "markdown") -> str:
        """格式化参考文献列表"""
```

#### 3.3.3 多知识库管理

**修改：`rag/service.py`**

- 支持多个知识库同时检索
- 知识库权限管理
- 知识库元数据管理

---

## 4. 目录结构规划

```
rag/
├── __init__.py              # 统一导出
├── types.py                 # 数据模型
├── routing.py               # 文件类型路由
├── service.py               # RAGService 统一入口
├── factory.py               # Pipeline 工厂
├── pipeline.py              # 可组合 Pipeline（可选）
│
├── parsers/                 # 文档解析器
│   ├── __init__.py
│   ├── base.py
│   ├── pdf.py
│   ├── markdown.py
│   └── text.py
│
├── chunkers/                # 文本分块器
│   ├── __init__.py
│   ├── base.py
│   ├── fixed.py
│   └── semantic.py
│
├── embedders/               # 嵌入模型
│   ├── __init__.py
│   ├── base.py
│   └── openai.py
│
├── indexers/                # 索引器
│   ├── __init__.py
│   ├── base.py
│   └── vector.py
│
├── retrievers/              # 检索器
│   ├── __init__.py
│   ├── base.py
│   ├── dense.py
│   └── smart.py
│
├── pipelines/               # 完整 Pipeline
│   ├── __init__.py
│   └── llamaindex.py
│
└── utils/                   # 工具函数
    ├── __init__.py
    ├── encoding.py          # 编码检测
    └── text.py              # 文本处理
```

---

## 5. 与现有代码的集成

### 5.1 向后兼容

- 保留现有 `embeddings.py`、`vectorstore.py`、`retriever.py` 接口
- 通过适配器模式逐步迁移
- 现有代码可继续工作

### 5.2 配置更新

**修改：`config/settings.py`**

```python
# 新增配置项
rag_provider: str = "llamaindex"  # llamaindex | langchain
rag_kb_base_dir: str = "./data/knowledge_bases"
rag_chunk_size: int = 512
rag_chunk_overlap: int = 50
rag_top_k: int = 5
rag_enable_rerank: bool = True
```

### 5.3 服务层集成

**修改：`services/document_service.py`**

集成 RAGService，支持：
- 文档自动索引
- 知识库检索
- 引用生成

---

## 6. 依赖管理

### 6.1 核心依赖

```toml
# 现有依赖
langchain-core = "*"
langchain-openai = "*"
chromadb = "*"

# 新增依赖
llama-index = "*"                    # LlamaIndex 核心
llama-index-vector-stores-chroma = "*"  # Chroma 集成
pymupdf = "*"                        # PDF 解析
markdown-it-py = "*"                 # Markdown 解析
chardet = "*"                        # 编码检测
```

### 6.2 可选依赖

```toml
# 高级功能
sentence-transformers = "*"          # 本地嵌入模型
rank-bm25 = "*"                      # BM25 检索
cohere = "*"                         # Cohere Rerank
```

---

## 7. 测试策略

### 7.1 单元测试

```
tests/rag/
├── test_parsers.py
├── test_chunkers.py
├── test_embedders.py
├── test_retrievers.py
└── test_service.py
```

### 7.2 集成测试

- 完整 Pipeline 测试
- 多文件类型处理测试
- 知识库生命周期测试

### 7.3 性能测试

- 大规模文档索引性能
- 检索延迟测试
- 内存占用测试

---

## 8. 实施优先级

| 优先级 | 任务 | 预计时间 | 依赖 |
|--------|------|----------|------|
| P0 | 数据模型定义 (types.py) | 0.5 天 | 无 |
| P0 | 文件路由 (routing.py) | 0.5 天 | 无 |
| P0 | PDF 解析器 | 1 天 | routing |
| P0 | 基础分块器 | 1 天 | 无 |
| P1 | LlamaIndex Pipeline | 2 天 | 解析器、分块器 |
| P1 | RAGService 统一接口 | 1 天 | Pipeline |
| P1 | 与现有系统集成 | 1 天 | RAGService |
| P2 | 智能检索 | 2 天 | RAGService |
| P2 | 引用管理 | 1 天 | 智能检索 |
| P3 | 多知识库管理 | 2 天 | RAGService |

---

## 9. 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| LlamaIndex 学习曲线 | 中 | 参考 DeepTutor 实现，逐步迁移 |
| PDF 解析准确性 | 中 | 使用 PyMuPDF，保留原始文本对比 |
| 向量存储兼容性 | 低 | 保留 Chroma 支持，逐步测试 |
| 性能问题 | 中 | 异步处理，批量操作，缓存机制 |
| 依赖冲突 | 低 | 使用虚拟环境，锁定版本 |

---

## 10. 成功标准

### 10.1 功能标准

- [ ] 支持 PDF、Markdown、文本文件导入
- [ ] 支持至少 2 种分块策略
- [ ] 检索结果包含来源信息
- [ ] 支持增量文档添加
- [ ] 支持多知识库管理

### 10.2 性能标准

- [ ] 100 页 PDF 索引时间 < 30 秒
- [ ] 检索延迟 < 500ms
- [ ] 支持 1000+ 文档的知识库

### 10.3 代码标准

- [ ] 单元测试覆盖率 > 70%
- [ ] 所有公共接口有文档字符串
- [ ] 通过类型检查
- [ ] 向后兼容现有代码

---

## 附录：参考代码

### DeepTutor RAG 关键文件

```
e:\PythonProjects\DeepTutor\deeptutor\services\rag\
├── types.py                 # 数据模型参考
├── pipeline.py              # Pipeline 架构参考
├── factory.py               # 工厂模式参考
├── service.py               # 服务层参考
└── pipelines\llamaindex.py  # LlamaIndex 实现参考
```

### 关键学习点

1. **组件化设计**：每个处理环节都是独立组件，通过 Protocol 定义接口
2. **文件路由**：集中处理文件类型分类，避免重复逻辑
3. **异步处理**：所有 I/O 操作使用 async/await
4. **错误处理**：详细的日志记录和错误传播
5. **配置管理**：通过 settings 统一管理配置
