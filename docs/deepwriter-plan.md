# DeepWriter 写手 Agent 规划文档

## 1. 项目定位

`DeepWriter` 的目标不是做一个“单轮改写工具”，而是打造一个基于 LangChain/LangGraph 的、面向真实写作流程的 `writer agent` 平台。

它需要覆盖从“理解需求”到“资料准备”到“生成初稿”到“多轮修改”到“事实核查/风格统一”到“版本沉淀”的完整闭环，而不是只输出一次文本。

结合当前项目基座与 `../Deeptutor` 的设计经验，建议将 `DeepWriter` 定位为：

- 一个以写作为核心场景的 `agent-native` 系统
- 一个支持多阶段工作流的内容生产平台
- 一个可扩展到多能力模式的统一运行时
- 一个可沉淀用户风格、知识库、项目上下文的长期写作助手

## 2. 建设目标

### 2.1 产品目标

- 支持常见写作任务：文章、博客、报告、方案、邮件、营销文案、知识内容
- 支持多轮协作：规划、起草、改写、扩写、压缩、续写、润色、校对
- 支持资料增强：知识库检索、网页搜索、参考素材整合
- 支持长文写作：分段生成、章节管理、上下文压缩、版本迭代
- 支持个性化：用户写作风格、品牌语气、术语偏好、禁用表达
- 支持工程化接入：CLI、API、Web UI、后续插件能力

### 2.2 技术目标

- 建立统一的 Agent 抽象层，而不是只保留单个 `WriterAgent`
- 建立可切换的能力层，便于后续扩展为“写作规划”“深度研究”“协作编辑”等模式
- 建立统一 Prompt 管理、配置管理、会话管理、工具注册机制
- 建立可观察性能力：日志、trace、token 统计、阶段输出
- 建立可测试、可演进的模块边界，避免早期代码耦合失控

## 3. 当前基座评估

当前 `DeepWriter` 已具备最小可运行骨架：

- `config/settings.py`：基础配置与多供应商 LLM 参数
- `llm/factory.py`：LLM 工厂，已支持多 provider
- `rag/`：Embedding、Vector Store、Retriever 的初始封装
- `agents/base.py`：Agent 基类与状态对象
- `agents/writer.py`：一个最小写作 Agent 示例

当前优势：

- 分层方向是对的，已经有 `config`、`llm`、`rag`、`agent` 四层雏形
- 技术栈与目标匹配，已选择 LangChain/LangGraph
- provider 抽象提前做了，对后续扩展很有帮助

当前缺口：

- 只有“单 Agent + 单 prompt + 单轮生成”，没有真实写作 workflow
- 没有统一的 prompt 目录与加载机制
- 没有工具注册与工具可用性描述
- 没有会话持久化、草稿管理、版本管理
- 没有能力层和 orchestrator，后续一扩展就容易散
- `rag` 只有底层封装，没有完整 ingestion 和检索编排
- 没有测试目录、没有运行模式、没有 API/CLI 交付入口

结论：

当前项目适合立刻进入“架构定型 + 第一批核心能力建设”阶段，不建议继续沿着单一 `WriterAgent.execute()` 线性堆逻辑。

## 4. 从 Deeptutor 借鉴的设计范式

结合 `../Deeptutor`，建议优先借鉴以下设计，而不是照搬全部功能。

### 4.1 借鉴一：能力层高于 Agent 层

`Deeptutor` 的核心经验之一，是把“面向用户的功能模块”抽象成 capability，再由 capability 内部组织 agent、tool、session、stream。

对 `DeepWriter` 而言，建议区分：

- `Capability`：用户看到的写作模式
- `Agent`：能力内部的执行角色
- `Tool`：可调用的外部工具
- `Workflow/Graph`：将多个 agent/tool 串成完整过程

建议首批 capability：

- `chat_writer`：通用写作对话
- `draft_writer`：根据 brief 产出结构化初稿
- `editor`：改写、扩写、缩写、润色、校对
- `research_writer`：先检索后写作
- `longform_writer`：长文/章节型写作

### 4.2 借鉴二：统一 PromptManager

`Deeptutor` 的 prompt 管理是非常值得迁移的模式。`DeepWriter` 也应尽早统一 prompt 的存储、加载、缓存与语言回退机制。

建议目录形态：

```text
deepwriter/
  agents/
    writer/
      prompts/
        zh/
          planner.yaml
          drafter.yaml
          editor.yaml
          reviewer.yaml
        en/
          planner.yaml
          drafter.yaml
          editor.yaml
          reviewer.yaml
```

建议 prompt 管理能力：

- 多语言加载与回退
- 按 agent 名称加载
- 支持模板变量格式化
- 支持热刷新或缓存失效
- 支持 prompt 版本管理

### 4.3 借鉴三：统一运行时和注册中心

`Deeptutor` 的 `orchestrator + registry` 模式很适合 `DeepWriter`。

建议新增：

- `runtime/orchestrator.py`：统一入口，负责路由 capability
- `runtime/registry/capability_registry.py`
- `runtime/registry/tool_registry.py`

这样可以避免未来出现：

- CLI 一套调度逻辑
- API 一套调度逻辑
- Web UI 一套调度逻辑

统一运行时后，CLI、API、Web 只是入口层，底层逻辑共用。

### 4.4 借鉴四：统一 Session 与上下文管理

写作场景比问答更依赖长期上下文，因此建议尽早引入统一会话模型。

每个 session 至少要保存：

- 用户原始需求
- 当前文档内容
- 文档版本历史
- 已启用工具
- 选定知识库
- 写作风格配置
- 阶段中间产物，例如大纲、素材卡片、事实清单

推荐能力：

- 会话持久化
- 草稿自动保存
- 版本快照
- 变更 diff
- 恢复到指定版本

### 4.5 借鉴五：阶段式 Pipeline，而不是一次性生成

`Deeptutor` 在研究和解题模块里大量使用分阶段 pipeline，这一点对长写作尤其重要。

建议将写作流程拆成典型阶段：

1. `intent_parse`：解析任务与目标读者
2. `plan`：生成写作计划与大纲
3. `research`：补资料、抽事实、整理引用
4. `draft`：生成首稿
5. `review`：检查结构、事实、语气、冗余
6. `revise`：按反馈修订
7. `export`：输出为 markdown/html/plaintext

## 5. DeepWriter 目标能力地图

## 5.1 核心能力

### A. 对话写作

适用场景：

- 用户一句话提出需求，快速得到可用内容
- 支持追问补全需求
- 支持继续改写和多轮迭代

能力要求：

- 意图识别
- 写作任务分类
- 自动补齐缺失参数
- 上下文连续对话

### B. 结构化初稿生成

适用场景：

- 博客、方案、报告、演讲稿、公众号文章

能力要求：

- 从 brief 自动抽取主题、目标读者、目的、字数、语气、格式
- 先出大纲，再出正文
- 支持按章节流式生成

### C. 协作编辑

适用场景：

- 改写、润色、压缩、扩写、换风格、提高清晰度

能力要求：

- 局部编辑
- 保持原意
- 支持“只改表达不改结构”
- 支持“按品牌语气改写”
- 输出编辑说明与 diff 摘要

### D. 研究增强写作

适用场景：

- 行业分析、综述、观点文、带引用内容

能力要求：

- 接知识库检索
- 接网页搜索
- 生成参考摘要卡片
- 区分“事实”与“观点”
- 输出引用来源和参考材料

### E. 长文工作流

适用场景：

- 长报告、系列文章、电子书、课程讲义

能力要求：

- 文档拆章
- 章节间上下文压缩
- 角色分工协作
- 大纲锁定与局部重写
- 全局一致性检查

## 5.2 增强能力

- 风格库：如专业、故事化、品牌型、学术型、社媒型
- 用户画像：术语偏好、常用句式、禁忌表达
- 模板系统：文章模板、邮件模板、方案模板
- 事实核查：关键结论、数字、时间、引用一致性
- SEO 辅助：标题、摘要、关键词、元描述
- 多格式导出：Markdown、HTML、富文本片段
- 评价系统：可读性、结构完整性、目标匹配度

## 6. 推荐架构

建议按“入口层 - 运行时层 - 能力层 - 服务层 - 基础设施层”组织。

### 6.1 分层结构

```text
DeepWriter
├─ interfaces/
│  ├─ cli/
│  ├─ api/
│  └─ web/                  # 后续可加
├─ runtime/
│  ├─ orchestrator.py
│  └─ registry/
├─ capabilities/
│  ├─ chat_writer.py
│  ├─ draft_writer.py
│  ├─ editor.py
│  ├─ research_writer.py
│  └─ longform_writer.py
├─ agents/
│  ├─ base.py
│  ├─ planner.py
│  ├─ drafter.py
│  ├─ editor.py
│  ├─ reviewer.py
│  └─ researcher.py
├─ services/
│  ├─ prompt/
│  ├─ llm/
│  ├─ embedding/
│  ├─ rag/
│  ├─ session/
│  ├─ memory/
│  └─ export/
├─ tools/
│  ├─ rag_search.py
│  ├─ web_search.py
│  ├─ outline.py
│  ├─ rewrite.py
│  └─ citation.py
├─ storage/
│  ├─ documents/
│  ├─ sessions/
│  └─ vectorstores/
└─ docs/
```

### 6.2 运行时职责

`orchestrator` 负责：

- 根据请求选择 capability
- 注入上下文、session、tool、config
- 管理流式输出
- 收集阶段事件与 trace
- 对外暴露统一接口

`capability` 负责：

- 定义当前模式的执行流程
- 组织一个或多个 agent
- 决定是否使用 RAG、Web、记忆、模板

`agent` 负责：

- 执行单一职责任务
- 使用统一 prompt 和统一 LLM 调用接口

### 6.3 推荐 Agent 角色

建议首批拆成 4 个基础角色：

- `PlannerAgent`：把模糊需求转成可执行写作计划
- `ResearchAgent`：收集与整理资料
- `DraftAgent`：生成初稿
- `ReviewAgent`：检查结构、事实、风格、冗余

第二阶段再补：

- `EditorAgent`：专门负责局部改写
- `StyleAgent`：负责风格对齐
- `CitationAgent`：负责引用格式与事实来源整理
- `OutlineAgent`：负责章节规划与重排

## 7. LangChain / LangGraph 落地建议

### 7.1 LangChain 适合承担的部分

- 模型调用抽象
- PromptTemplate / ChatPromptTemplate
- Tool 封装
- Retriever 封装
- 文档处理链

### 7.2 LangGraph 适合承担的部分

- 多阶段状态图
- 可回退的工作流
- 条件分支
- 人工确认节点
- 长文生成中的循环修订

建议不要一开始就把所有流程都图化，而是按下面节奏推进：

1. 第一阶段用普通 Python workflow 跑通主链路
2. 第二阶段把长文写作、研究写作迁移到 LangGraph
3. 第三阶段再加入人工审批节点、失败重试、状态恢复

## 8. 数据模型建议

建议尽早定义核心数据结构，而不是依赖松散 dict。

### 8.1 写作请求

```python
class WritingRequest(BaseModel):
    task_type: str
    topic: str
    audience: str | None = None
    goal: str | None = None
    tone: str | None = None
    length: str | None = None
    language: str = "zh"
    use_rag: bool = False
    use_web: bool = False
    session_id: str | None = None
```

### 8.2 写作状态

```python
class WritingState(BaseModel):
    request: WritingRequest
    outline: list[str] = []
    research_notes: list[dict] = []
    draft_sections: list[str] = []
    review_feedback: list[str] = []
    final_text: str = ""
    metadata: dict[str, Any] = {}
```

### 8.3 文档版本

```python
class DocumentVersion(BaseModel):
    document_id: str
    version: int
    title: str
    content: str
    change_summary: str | None = None
    created_at: datetime
```

## 9. 核心模块规划

### 9.1 Prompt 系统

建议新增：

- `services/prompt/manager.py`
- `agents/<name>/prompts/zh/*.yaml`
- `agents/<name>/prompts/en/*.yaml`

目标：

- prompt 文件化
- 多语言
- 支持缓存
- 支持 fallback
- 支持 agent 级隔离

### 9.2 Session 与草稿管理

建议新增：

- `services/session/base.py`
- `services/session/file_store.py`
- `services/session/manager.py`

保存内容：

- 对话历史
- 当前文档
- 历史版本
- 中间大纲
- 用户配置

### 9.3 RAG 管道

当前已有底层向量检索封装，但还缺：

- 文档导入
- chunking
- metadata 设计
- 多知识库支持
- 检索结果重排
- 引用片段回传

建议能力拆分：

- `parsers`：markdown/text/pdf
- `chunkers`：fixed/semantic
- `indexers`：chroma/faiss
- `retrievers`：dense/hybrid
- `pipelines`：ingest/query

### 9.4 工具层

建议工具定义成可注册对象，而不是散落函数。

首批工具：

- `rag_search`
- `web_search`
- `outline_generate`
- `style_rewrite`
- `citation_format`
- `document_diff`

### 9.5 可观察性

建议尽早加上：

- 请求日志
- Agent 阶段日志
- token 统计
- tool 调用记录
- 错误归因
- trace_id / session_id

## 10. 分阶段实施路线

## Phase 0：架构定型

目标：

- 明确目录结构
- 明确 capability/agent/tool/service 边界
- 完成规划文档与基础开发规范

交付物：

- `docs/deepwriter-plan.md`
- 新目录骨架
- 统一数据模型定义

## Phase 1：最小可用写作链路

目标：

- 从用户输入到首稿输出跑通
- 支持基础 prompt 管理
- 支持 CLI 演示

范围：

- `PlannerAgent`
- `DraftAgent`
- `chat_writer` 或 `draft_writer` capability
- PromptManager
- 基础 session 持久化

验收标准：

- 输入 brief 能生成大纲和初稿
- 能保存 session
- 能连续多轮改写

## Phase 2：协作编辑能力

目标：

- 让系统从“能写”升级到“能改”

范围：

- `EditorAgent`
- `ReviewAgent`
- 局部文本编辑
- 扩写/缩写/润色/改语气
- diff 与修改摘要

验收标准：

- 支持选中文本局部改写
- 支持“保持原意”的润色模式
- 支持输出修改说明

## Phase 3：研究增强写作

目标：

- 让内容生成建立在可引用资料上

范围：

- 知识库导入与检索
- Web Search 工具接入
- `ResearchAgent`
- 引用片段与参考列表

验收标准：

- 写作前可自动检索资料
- 输出内容可附带参考来源
- 能区分“事实依据”和“主观表达”

## Phase 4：长文与 LangGraph

目标：

- 支持章节型、可恢复、可审阅的长文生产

范围：

- LangGraph 工作流
- 分章节状态管理
- 人工确认节点
- 失败重试和断点恢复

验收标准：

- 支持超过 3000 字的稳定生成
- 支持章节重写
- 支持从中间状态恢复

## Phase 5：产品化交付

目标：

- 从开发项目升级为可被真实使用的产品

范围：

- FastAPI 接口
- Web 编辑器
- 模板市场
- 风格库
- 用户配置页

验收标准：

- 提供 API 和基础前端
- 支持项目级写作工作台
- 支持用户管理自己的模板/风格/知识库

## 11. 近期优先级建议

如果按投入产出比排序，建议优先做下面 8 项：

1. 重构目录，补齐 `capabilities`、`services/prompt`、`services/session`
2. 引入 `PromptManager`
3. 将 `WriterAgent` 拆为 `PlannerAgent + DraftAgent + ReviewAgent`
4. 增加统一 `WritingRequest/WritingState` 数据模型
5. 新增 CLI 入口，跑通“需求 -> 大纲 -> 初稿”
6. 补齐 RAG ingestion 流程
7. 增加基础日志和 trace
8. 为核心链路补 3 到 5 个高价值测试

## 12. 测试策略建议

建议遵循“高价值、低噪音”原则。

优先测试：

- PromptManager 的加载与 fallback
- AgentRegistry / CapabilityRegistry 注册逻辑
- 写作请求到状态转换
- session 持久化
- RAG 检索接口契约
- 核心 capability 的 happy path

不建议早期投入太多的部分：

- 大量依赖真实 LLM 输出文案的脆弱测试
- 对提示词内容逐字匹配的测试
- 大量端到端长链路快照测试

## 13. 风险与注意事项

- 不要过早把所有功能都做成多 Agent，先确保“单链路稳定”
- 不要把业务逻辑散落在 prompt 中，关键流程规则应留在代码层
- 不要把 `rag` 仅仅当成“检索一段文本”，要尽早考虑引用与来源结构
- 不要直接把 `Deeptutor` 的教育场景模块硬搬过来，要只迁移通用范式
- 不要一开始就强依赖 Web UI，先用 CLI/API 验证能力模型
