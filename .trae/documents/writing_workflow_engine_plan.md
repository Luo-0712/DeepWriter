# DeepWriter 写作工作流引擎开发计划

## 1. 项目概述

### 1.1 目标
构建基于 LangGraph 的写作工作流引擎，实现从需求理解到最终输出的完整写作流程。

### 1.2 核心特性
- **多阶段工作流**：规划 → 研究 → 起草 → 编辑 → 校对
- **多 Agent 协作**：Planner、Researcher、Writer、Editor、Critic
- **人机协作**：支持用户在中途干预和修改
- **状态持久化**：支持断点续写和版本回滚
- **灵活配置**：支持不同写作场景的流程定制

---

## 2. 架构设计

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                      WritingOrchestrator                        │
│                     (工作流编排器 - LangGraph)                   │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │ Planner  │→ │Researcher│→ │  Writer  │→ │  Editor  │        │
│  │  (规划)  │  │ (研究)   │  │ (起草)   │  │ (编辑)   │        │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘        │
│       ↑                                      ↓                  │
│       └────────────── Critic (评审) ←────────┘                  │
├─────────────────────────────────────────────────────────────────┤
│                      State Management                           │
│              (WritingState + SessionManager)                    │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 目录结构

```
workflows/
├── __init__.py
├── base.py                 # 工作流基类与状态定义
├── graph.py               # LangGraph 状态图定义
├── orchestrator.py        # 工作流编排器
├── nodes/                 # 工作流节点实现
│   ├── __init__.py
│   ├── planner.py         # 规划节点
│   ├── researcher.py      # 研究节点
│   ├── writer.py          # 写作节点
│   ├── editor.py          # 编辑节点
│   └── critic.py          # 评审节点
├── conditions.py          # 条件路由逻辑
└── prompts/               # 工作流专用 prompts
    ├── zh/
    │   ├── planner.yaml
    │   ├── researcher.yaml
    │   ├── writer.yaml
    │   ├── editor.yaml
    │   └── critic.yaml
    └── en/
        └── ...

agents/
└── specialized/           # 专业化 Agent
    ├── __init__.py
    ├── planner_agent.py
    ├── researcher_agent.py
    ├── writer_agent.py
    ├── editor_agent.py
    └── critic_agent.py
```

---

## 3. 数据模型设计

### 3.1 工作流状态 (WorkflowState)

```python
class WorkflowState(BaseModel):
    """工作流状态 - LangGraph 状态对象"""

    # 输入
    request: WritingRequest
    user_input: str

    # 中间产物
    outline: Optional[Outline] = None           # 大纲
    research_results: List[ResearchNote] = []   # 研究结果
    draft_sections: List[DraftSection] = []     # 草稿章节
    edit_suggestions: List[EditSuggestion] = [] # 编辑建议
    review_feedback: Optional[ReviewFeedback] = None  # 评审反馈

    # 输出
    final_content: str = ""

    # 控制
    current_stage: str = "init"                 # 当前阶段
    stage_history: List[str] = []               # 阶段历史
    should_continue: bool = True                # 是否继续
    user_intervention: Optional[UserIntervention] = None  # 用户干预

    # 元数据
    metadata: Dict[str, Any] = {}
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
```

### 3.2 扩展数据类型

```python
class Outline(BaseModel):
    """文章大纲"""
    title: str
    sections: List[Section]
    estimated_length: str
    target_audience: str
    key_points: List[str]

class Section(BaseModel):
    """章节定义"""
    id: str
    title: str
    description: str
    estimated_words: int
    key_points: List[str]

class ResearchNote(BaseModel):
    """研究笔记"""
    query: str
    source: str  # "rag" | "web" | "kb"
    content: str
    relevance_score: float
    metadata: Dict[str, Any]

class DraftSection(BaseModel):
    """草稿章节"""
    section_id: str
    title: str
    content: str
    word_count: int
    status: str  # "draft" | "revised" | "final"

class EditSuggestion(BaseModel):
    """编辑建议"""
    section_id: str
    type: str  # "grammar" | "style" | "structure" | "content"
    original: str
    suggestion: str
    reason: str

class ReviewFeedback(BaseModel):
    """评审反馈"""
    overall_score: float
    strengths: List[str]
    weaknesses: List[str]
    suggestions: List[str]
    should_revise: bool
```

---

## 4. 工作流节点实现

### 4.1 规划节点 (Planner Node)

**职责**：
- 分析用户需求
- 生成文章大纲
- 确定写作策略

**输入**：WritingRequest + user_input
**输出**：Outline

**Prompt 设计**：
```yaml
system: |
  你是一位专业的写作规划师。你的任务是根据用户需求，制定详细的写作计划。

  你需要：
  1. 分析用户意图和目标读者
  2. 确定文章结构和章节安排
  3. 为每个章节设定关键要点和字数
  4. 提供写作策略建议

  输出格式必须是结构化的 JSON。

human: |
  请为以下写作任务制定大纲：

  主题：{topic}
  类型：{task_type}
  目标读者：{audience}
  期望长度：{length}
  语气风格：{tone}

  额外要求：
  {extra_context}
```

### 4.2 研究节点 (Researcher Node)

**职责**：
- 根据大纲确定研究需求
- 执行 RAG 检索和网络搜索
- 整理研究笔记

**输入**：Outline + WritingRequest
**输出**：List[ResearchNote]

**功能**：
- 自动判断是否需要检索
- 支持多源检索（RAG + Web）
- 结果去重和相关性排序

### 4.3 写作节点 (Writer Node)

**职责**：
- 根据大纲和研究结果生成内容
- 支持分章节生成
- 保持上下文一致性

**输入**：Outline + ResearchNotes
**输出**：List[DraftSection]

**策略**：
- 逐章节生成，每章独立调用 LLM
- 使用大纲中的关键要点作为约束
- 引用研究笔记中的素材

### 4.4 编辑节点 (Editor Node)

**职责**：
- 检查语法和风格
- 优化表达和结构
- 确保一致性

**输入**：DraftSections
**输出**：EditSuggestions + 修订后的内容

**编辑维度**：
1. 语法检查
2. 风格统一
3. 逻辑连贯
4. 字数控制

### 4.5 评审节点 (Critic Node)

**职责**：
- 评估整体质量
- 判断是否满足需求
- 决定是否需要返工

**输入**：完整草稿 + 原始需求
**输出**：ReviewFeedback

**评审标准**：
- 内容完整性
- 逻辑清晰度
- 语言流畅度
- 目标达成度

---

## 5. 工作流图定义

### 5.1 基础工作流

```python
def create_basic_workflow() -> StateGraph:
    """创建基础写作工作流"""

    workflow = StateGraph(WorkflowState)

    # 添加节点
    workflow.add_node("planner", planner_node)
    workflow.add_node("researcher", researcher_node)
    workflow.add_node("writer", writer_node)
    workflow.add_node("editor", editor_node)
    workflow.add_node("critic", critic_node)
    workflow.add_node("human_review", human_review_node)

    # 设置入口
    workflow.set_entry_point("planner")

    # 添加边
    workflow.add_edge("planner", "researcher")
    workflow.add_edge("researcher", "writer")
    workflow.add_edge("writer", "editor")
    workflow.add_edge("editor", "critic")

    # 条件边：评审结果决定下一步
    workflow.add_conditional_edges(
        "critic",
        should_continue_or_revise,
        {
            "revise": "writer",      # 需要修改，返回写作
            "human_review": "human_review",  # 需要人工审核
            "finish": END            # 完成
        }
    )

    # 人工审核后的路由
    workflow.add_conditional_edges(
        "human_review",
        process_human_feedback,
        {
            "approve": END,
            "revise": "writer",
            "edit": "editor"
        }
    )

    return workflow.compile()
```

### 5.2 条件路由函数

```python
def should_continue_or_revise(state: WorkflowState) -> str:
    """根据评审结果决定下一步"""
    feedback = state.review_feedback

    if not feedback:
        return "finish"

    # 质量分数低于阈值，需要重写
    if feedback.overall_score < 0.6:
        return "revise"

    # 需要人工确认
    if feedback.should_revise:
        return "human_review"

    return "finish"

def process_human_feedback(state: WorkflowState) -> str:
    """处理人工反馈"""
    intervention = state.user_intervention

    if not intervention:
        return "approve"

    if intervention.action == "approve":
        return "approve"
    elif intervention.action == "revise":
        return "revise"
    elif intervention.action == "edit":
        return "edit"

    return "approve"
```

---

## 6. 人机协作机制

### 6.1 干预点设计

```python
class UserIntervention(BaseModel):
    """用户干预"""
    action: str  # "approve" | "revise" | "edit" | "pause"
    stage: str   # 干预发生的阶段
    feedback: str
    specific_changes: Optional[Dict[str, Any]] = None

class HumanReviewNode:
    """人工审核节点"""

    async def __call__(self, state: WorkflowState) -> WorkflowState:
        """暂停工作流，等待用户输入"""

        # 保存当前状态
        await self._save_checkpoint(state)

        # 生成审核报告
        review_report = self._generate_review_report(state)

        # 抛出中断，等待用户
        raise HumanInterrupt(
            message="请审核当前内容",
            report=review_report,
            state=state
        )

    def _generate_review_report(self, state: WorkflowState) -> Dict:
        """生成审核报告"""
        return {
            "current_stage": state.current_stage,
            "outline": state.outline,
            "draft_preview": self._get_draft_preview(state),
            "review_feedback": state.review_feedback,
            "options": [
                {"action": "approve", "label": "确认完成"},
                {"action": "revise", "label": "要求重写"},
                {"action": "edit", "label": "编辑修改"}
            ]
        }
```

### 6.2 断点续写

```python
class WorkflowCheckpoint(BaseModel):
    """工作流检查点"""
    checkpoint_id: str
    workflow_id: str
    state: WorkflowState
    created_at: datetime

class CheckpointManager:
    """检查点管理器"""

    async def save_checkpoint(self, state: WorkflowState) -> str:
        """保存检查点"""
        checkpoint = WorkflowCheckpoint(
            checkpoint_id=str(uuid.uuid4()),
            workflow_id=state.metadata.get("workflow_id"),
            state=state,
            created_at=datetime.now()
        )
        # 保存到数据库
        await self._persist(checkpoint)
        return checkpoint.checkpoint_id

    async def resume_from_checkpoint(
        self,
        checkpoint_id: str,
        user_intervention: UserIntervention
    ) -> WorkflowState:
        """从检查点恢复"""
        checkpoint = await self._load(checkpoint_id)
        state = checkpoint.state
        state.user_intervention = user_intervention
        state.should_continue = True
        return state
```

---

## 7. 实现步骤

### Phase 1: 基础架构 (第 1-2 天)

**任务 1.1**: 创建工作流目录结构
- [ ] 创建 `workflows/` 目录及子目录
- [ ] 创建 `agents/specialized/` 目录
- [ ] 创建 `workflows/prompts/` 目录结构

**任务 1.2**: 定义工作流数据模型
- [ ] 创建 `workflows/base.py`
- [ ] 定义 `WorkflowState`
- [ ] 定义 `Outline`, `ResearchNote`, `DraftSection` 等类型
- [ ] 定义 `UserIntervention`

**任务 1.3**: 扩展 WritingState
- [ ] 在 `services/models.py` 添加工作流相关字段
- [ ] 添加 `workflow_id`, `current_stage`, `stage_history`

### Phase 2: 专业化 Agent (第 3-4 天)

**任务 2.1**: 创建 Planner Agent
- [ ] 实现 `agents/specialized/planner_agent.py`
- [ ] 实现大纲生成功能
- [ ] 添加 planner prompt

**任务 2.2**: 创建 Researcher Agent
- [ ] 实现 `agents/specialized/researcher_agent.py`
- [ ] 集成 RAG 和搜索工具
- [ ] 实现研究笔记整理

**任务 2.3**: 创建 Writer Agent
- [ ] 实现 `agents/specialized/writer_agent.py`
- [ ] 实现分章节写作
- [ ] 添加 writer prompt

**任务 2.4**: 创建 Editor Agent
- [ ] 实现 `agents/specialized/editor_agent.py`
- [ ] 实现多维度编辑检查
- [ ] 添加 editor prompt

**任务 2.5**: 创建 Critic Agent
- [ ] 实现 `agents/specialized/critic_agent.py`
- [ ] 实现质量评估
- [ ] 添加 critic prompt

### Phase 3: 工作流节点 (第 5-6 天)

**任务 3.1**: 实现工作流节点
- [ ] `workflows/nodes/planner.py`
- [ ] `workflows/nodes/researcher.py`
- [ ] `workflows/nodes/writer.py`
- [ ] `workflows/nodes/editor.py`
- [ ] `workflows/nodes/critic.py`

**任务 3.2**: 实现条件路由
- [ ] 创建 `workflows/conditions.py`
- [ ] 实现 `should_continue_or_revise`
- [ ] 实现 `process_human_feedback`

### Phase 4: 工作流编排 (第 7-8 天)

**任务 4.1**: 实现状态图
- [ ] 创建 `workflows/graph.py`
- [ ] 定义基础工作流
- [ ] 定义研究增强工作流

**任务 4.2**: 实现编排器
- [ ] 创建 `workflows/orchestrator.py`
- [ ] 实现 `WritingOrchestrator` 类
- [ ] 集成 SessionManager

**任务 4.3**: 实现人机协作
- [ ] 实现 `HumanReviewNode`
- [ ] 实现 `CheckpointManager`
- [ ] 添加干预处理逻辑

### Phase 5: 集成与测试 (第 9-10 天)

**任务 5.1**: 集成到主程序
- [ ] 更新 `main.py` 支持工作流模式
- [ ] 添加工作流 CLI 命令
- [ ] 更新 `example_usage.py`

**任务 5.2**: 编写测试
- [ ] 创建 `tests/test_workflow.py`
- [ ] 测试各节点功能
- [ ] 测试完整工作流

**任务 5.3**: 编写文档
- [ ] 更新 `docs/` 工作流文档
- [ ] 添加使用示例
- [ ] 添加架构说明

---

## 8. 使用示例

### 8.1 基础用法

```python
from workflows.orchestrator import WritingOrchestrator
from services.models import WritingRequest

# 创建工作流编排器
orchestrator = WritingOrchestrator()

# 创建写作请求
request = WritingRequest(
    task_type="article",
    topic="人工智能在医疗领域的应用",
    audience="普通读者",
    length="medium",
    use_rag=True,
    use_web=True
)

# 执行工作流
result = await orchestrator.execute(
    request=request,
    user_input="请写一篇关于 AI 医疗的文章"
)

print(result.final_content)
```

### 8.2 人机协作用法

```python
# 执行工作流，在关键节点暂停
result = await orchestrator.execute(
    request=request,
    user_input="请写一篇关于 AI 医疗的文章",
    pause_on_stages=["outline", "draft"]  # 在大纲和草稿阶段暂停
)

# 查看大纲并修改
if result.current_stage == "outline":
    print("生成的大纲:", result.outline)

    # 用户修改大纲
    modified_outline = await get_user_modifications()

    # 继续执行
    result = await orchestrator.resume(
        intervention={
            "action": "edit",
            "stage": "outline",
            "specific_changes": {"outline": modified_outline}
        }
    )
```

### 8.3 断点续写

```python
# 启动工作流
workflow_id = await orchestrator.start(request, user_input)

# ... 程序中断 ...

# 恢复工作流
result = await orchestrator.resume_from_checkpoint(
    workflow_id=workflow_id,
    user_feedback="请增加更多技术细节"
)
```

---

## 9. 技术要点

### 9.1 LangGraph 集成

```python
from langgraph.graph import StateGraph, END
from langgraph.checkpoint import MemorySaver

# 使用检查点实现断点续写
memory = MemorySaver()
workflow = create_basic_workflow()
app = workflow.compile(checkpointer=memory)

# 运行工作流
config = {"configurable": {"thread_id": workflow_id}}
result = await app.ainvoke(initial_state, config)
```

### 9.2 状态管理

- 使用 Pydantic 模型定义状态，确保类型安全
- 每个节点返回完整状态对象，便于调试
- 使用 `stage_history` 追踪执行路径

### 9.3 错误处理

```python
class WorkflowError(Exception):
    """工作流错误"""
    pass

class NodeExecutionError(WorkflowError):
    """节点执行错误"""
    def __init__(self, node_name: str, original_error: Exception):
        self.node_name = node_name
        self.original_error = original_error
        super().__init__(f"Node {node_name} failed: {original_error}")
```

---

## 10. 验收标准

### 10.1 功能验收

- [ ] 能完整执行 Planning → Research → Writing → Editing → Critic 流程
- [ ] 支持在大纲、草稿阶段人工干预
- [ ] 支持断点续写和版本回滚
- [ ] 支持 RAG 和网络搜索增强
- [ ] 支持不同写作类型（文章、报告、故事等）

### 10.2 性能验收

- [ ] 单章节生成时间 < 10 秒
- [ ] 完整文章（3-5 章）生成时间 < 60 秒
- [ ] 支持并发执行多个工作流
- [ ] 内存占用合理，无内存泄漏

### 10.3 质量验收

- [ ] 大纲结构清晰，逻辑合理
- [ ] 内容紧扣主题，无跑题
- [ ] 章节之间过渡自然
- [ ] 编辑建议具体可操作
- [ ] 评审反馈准确反映内容质量

---

## 11. 后续扩展

### 11.1 短期扩展

1. **更多工作流模板**
   - 快速写作模式（跳过研究）
   - 深度研究模式（多轮检索）
   - 协作编辑模式（多人审核）

2. **可视化界面**
   - 工作流进度展示
   - 节点状态可视化
   - 实时预览草稿

### 11.2 长期规划

1. **自适应工作流**
   - 根据内容类型自动选择策略
   - 根据用户反馈优化流程

2. **多模态支持**
   - 图片生成和插入
   - 表格和数据可视化

3. **团队协作**
   - 角色分工（策划、写作、审核）
   - 版本对比和合并
