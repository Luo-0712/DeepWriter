# DeepWriter 验收测试指南

## 1. 快速启动测试

```bash
python test_chat.py
```

## 2. 测试清单

### 2.1 基础功能测试

| 测试项 | 操作 | 预期结果 |
|--------|------|----------|
| 启动检查 | 运行 `python test_chat.py` | 显示项目信息、LLM 信息、Agent 信息、SessionManager 信息 |
| 对话测试 | 输入任意写作需求 | WriterAgent 返回生成的内容 |
| 退出功能 | 输入 `quit` 或 `exit` | 正常退出程序 |

### 2.2 Prompt 管理测试

| 测试项 | 操作 | 预期结果 |
|--------|------|----------|
| 中文 Prompt | 默认启动后直接输入 | 使用中文 prompt 文件 |
| 英文 Prompt | 输入 `language en` 后对话 | 使用英文 prompt 文件 |
| 风格切换 | 输入 `style casual` | 写作风格切换为休闲风格 |

### 2.3 Session 管理测试

| 测试项 | 操作 | 预期结果 |
|--------|------|----------|
| 查看 Session | 输入 `session` | 显示当前 Session ID、消息数、版本数 |
| 查看状态 | 输入 `status` | 显示当前写作状态（主题、阶段、大纲数等） |
| 查看历史 | 输入 `history` | 显示最近 5 条消息历史 |
| 清空上下文 | 输入 `clear` | 重置 Agent 状态 |

### 2.4 数据模型测试

| 测试项 | 操作 | 预期结果 |
|--------|------|----------|
| WritingRequest | 对话时自动创建 | 包含 topic、style、language 等字段 |
| WritingState | 执行写作后 | 包含 draft_sections、final_text 等 |
| Session 持久化 | 检查 `data/sessions/` 目录 | 生成 JSON 格式的 Session 文件 |

## 3. 完整测试流程示例

```
# 1. 启动测试
python test_chat.py

# 2. 查看帮助
[You]: help

# 3. 测试对话
[You]: 写一篇关于 AI 发展的短文

# 4. 查看状态
[You]: status

# 5. 查看 Session
[You]: session

# 6. 查看历史
[You]: history

# 7. 切换风格
[You]: style creative

# 8. 继续对话
[You]: 继续写第二段

# 9. 清空上下文
[You]: clear

# 10. 退出
[You]: quit
```

## 4. 文件结构验证

检查以下文件是否存在：

```
DeepWriter/
├── services/
│   ├── __init__.py          # 导出所有模型和服务
│   ├── models.py            # 数据模型
│   ├── prompt/
│   │   ├── __init__.py
│   │   └── manager.py       # Prompt 管理器
│   └── session/
│       ├── __init__.py
│       ├── base.py          # Session 抽象
│       ├── file_store.py    # 文件存储
│       └── manager.py       # Session 管理器
├── agents/
│   └── writer/
│       └── prompts/
│           ├── zh/
│           │   └── system.yaml
│           └── en/
│               └── system.yaml
└── data/
    └── sessions/            # Session 存储目录
        └── *.json           # Session 文件
```

## 5. 代码检查点

### 5.1 数据模型 ([`services/models.py`](services/models.py:1))
- [ ] `WritingRequest` 包含所有必要字段
- [ ] `WritingState` 支持状态更新方法
- [ ] `DocumentVersion` 支持版本管理
- [ ] `SessionConfig` 支持会话配置

### 5.2 Prompt 管理 ([`services/prompt/manager.py`](services/prompt/manager.py:1))
- [ ] `load()` 支持多语言加载
- [ ] `get_system_prompt()` 支持变量格式化
- [ ] `clear_cache()` 支持缓存清除
- [ ] fallback 机制正常工作

### 5.3 Session 管理 ([`services/session/manager.py`](services/session/manager.py:1))
- [ ] `create_session()` 创建新 Session
- [ ] `load_session()` 加载已有 Session
- [ ] `save_session()` 持久化保存
- [ ] `start_writing()` 开始写作任务
- [ ] `add_message()` 添加消息历史

### 5.4 WriterAgent ([`agents/writer.py`](agents/writer.py:1))
- [ ] 集成 `PromptManager`
- [ ] 集成 `SessionManager`
- [ ] 支持 `WritingRequest` 参数
- [ ] 更新 `WritingState`

## 6. 常见问题排查

### 问题 1：Prompt 文件未找到
```
FileNotFoundError: Prompt not found for agent 'writer'
```
**解决**: 检查 `agents/writer/prompts/zh/system.yaml` 是否存在

### 问题 2：Session 存储目录不存在
```
FileNotFoundError: [Errno 2] No such file or directory: 'data/sessions'
```
**解决**: `FileSessionStore` 会自动创建目录，检查权限

### 问题 3：编码问题
```
UnicodeEncodeError: 'gbk' codec can't encode character
```
**解决**: Windows 终端使用 UTF-8，或设置 `PYTHONUTF8=1`

## 7. 验收标准

- [ ] 能够成功启动并显示所有初始化信息
- [ ] 能够进行正常对话并获取 LLM 响应
- [ ] 能够切换写作风格和语言
- [ ] 能够查看 Session 状态和历史
- [ ] Session 数据能够持久化到文件
- [ ] Prompt 能够从 YAML 文件正确加载
- [ ] 数据模型能够在对话中正确使用
