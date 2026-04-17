# 热切换配置支持计划

## 背景

当前项目存在配置缓存问题，`@lru_cache` 装饰的 `get_settings()` 导致运行时配置变更无法生效。本项目对热切换（运行时动态切换配置）有高需求，需要系统性改造。

## 现状分析

### 已发现的问题点

1. **settings.py**: `get_settings()` 使用 `@lru_cache`
2. **llm/factory.py**: `LLMFactory.create()` 使用 `get_settings()`
3. **services/rag/components/embedders/openai.py**: `OpenAIEmbedder` 使用 `get_settings()`
4. **services/rag/components/indexers/vector.py**: `VectorIndexer` 使用 `get_settings()`

### 缓存层级

```
Level 1: get_settings() - 配置对象缓存
    ↓
Level 2: LLMFactory._instances - LLM实例缓存
    ↓
Level 3: RAGFactory._PIPELINE_CACHE - Pipeline实例缓存
    ↓
Level 4: RAGService._pipeline - Service级别pipeline缓存
```

## 目标

实现真正的热切换支持：
1. 配置变更即时生效
2. 避免不必要的实例重建（性能优化）
3. 提供显式的缓存控制接口
4. 保持向后兼容

## 实施方案

### Phase 1: 配置层改造

**目标**: 移除 `get_settings()` 的缓存，但保留便捷性

**步骤**:
1. 修改 `get_settings()` 移除 `@lru_cache`
2. 添加 `get_settings_cached()` 保留缓存版本（用于性能敏感场景）
3. 添加配置变更监听机制（可选）

**文件**:
- `config/settings.py`

### Phase 2: LLM层改造

**目标**: LLM实例支持配置指纹，自动检测配置变更

**步骤**:
1. 修改 `LLMFactory.create()` 添加配置指纹检测
2. 配置指纹 = hash(provider + model + api_key + base_url)
3. 指纹不匹配时自动创建新实例
4. 保留 `force_new` 参数用于强制刷新

**文件**:
- `llm/factory.py`

### Phase 3: RAG层改造

**目标**: RAG Pipeline 支持热切换

**步骤**:
1. 修改 `RAGFactory.get_pipeline()` 添加配置指纹
2. 修改 `RAGService` 支持重新初始化 pipeline
3. 添加 `RAGService.reload()` 方法
4. Embedder 和 Indexer 同步改造

**文件**:
- `services/rag/factory.py`
- `services/rag/service.py`
- `services/rag/components/embedders/openai.py`
- `services/rag/components/indexers/vector.py`

### Phase 4: 事件通知机制（可选增强）

**目标**: 配置变更自动通知相关组件

**步骤**:
1. 添加配置变更事件总线
2. 组件订阅配置变更事件
3. 自动触发实例重建

**文件**:
- 新增 `config/events.py`

### Phase 5: API层支持

**目标**: 提供运行时配置切换接口

**步骤**:
1. 添加配置更新 API 端点
2. 添加实例状态查询 API
3. 添加缓存清理 API

**文件**:
- `api/routes/config.py` (新增)

## 详细设计

### 配置指纹机制

```python
class ConfigFingerprint:
    """配置指纹，用于检测配置变更"""
    
    @staticmethod
    def from_settings(settings: Settings) -> str:
        """从Settings生成指纹"""
        key_parts = [
            settings.llm_provider.value,
            settings.llm_model_name,
            settings.openai_api_key or "",
            settings.openai_api_base or "",
            settings.qwen_api_key or "",
            settings.qwen_api_base or "",
            # ... 其他关键配置
        ]
        return hashlib.md5("|".join(key_parts).encode()).hexdigest()[:16]
```

### LLMFactory 改造

```python
class LLMFactory:
    _instances: dict[str, BaseChatModel] = {}
    _config_fingerprints: dict[str, str] = {}  # 新增：配置指纹缓存
    
    @classmethod
    def create(cls, settings: Optional[Settings] = None, force_new: bool = False) -> BaseChatModel:
        settings = settings or Settings()  # 不再使用 get_settings()
        
        # 生成当前配置指纹
        current_fingerprint = ConfigFingerprint.from_settings(settings)
        cache_key = f"{settings.llm_provider.value}:{settings.llm_model_name}"
        
        # 检查是否需要重建实例
        if not force_new and cache_key in cls._instances:
            cached_fingerprint = cls._config_fingerprints.get(cache_key)
            if cached_fingerprint == current_fingerprint:
                return cls._instances[cache_key]
            else:
                logger.info(f"Config changed for {cache_key}, rebuilding LLM instance")
        
        # 创建新实例
        llm = cls._create_llm(settings)
        cls._instances[cache_key] = llm
        cls._config_fingerprints[cache_key] = current_fingerprint
        return llm
    
    @classmethod
    def clear_cache(cls) -> None:
        """清空所有缓存"""
        cls._instances.clear()
        cls._config_fingerprints.clear()
```

### RAGService 改造

```python
class RAGService:
    def __init__(self, kb_base_dir: Optional[str] = None, provider: Optional[str] = None):
        self.kb_base_dir = kb_base_dir or DEFAULT_KB_BASE_DIR
        self.provider = provider or "default"
        self._pipeline = None
        self._config_fingerprint = None  # 新增
        
    def _get_pipeline(self):
        """获取pipeline，自动检测配置变更"""
        current_fingerprint = ConfigFingerprint.from_settings(Settings())
        
        if self._pipeline is None or self._config_fingerprint != current_fingerprint:
            logger.info("RAG configuration changed, rebuilding pipeline")
            self._pipeline = get_pipeline(
                self.provider,
                kb_base_dir=self.kb_base_dir,
                use_cache=False  # 强制创建新实例
            )
            self._config_fingerprint = current_fingerprint
        
        return self._pipeline
    
    def reload(self) -> None:
        """强制重新加载配置和pipeline"""
        self._pipeline = None
        self._config_fingerprint = None
        clear_pipeline_cache()
```

## 任务清单

### Phase 1: 配置层
- [ ] 修改 `config/settings.py` - 移除 `@lru_cache`，添加 `get_settings_cached()`

### Phase 2: LLM层
- [ ] 修改 `llm/factory.py` - 实现配置指纹机制
- [ ] 添加 `ConfigFingerprint` 工具类

### Phase 3: RAG层
- [ ] 修改 `services/rag/factory.py` - 支持配置指纹
- [ ] 修改 `services/rag/service.py` - 支持自动检测和热重载
- [ ] 修改 `services/rag/components/embedders/openai.py` - 使用新配置机制
- [ ] 修改 `services/rag/components/indexers/vector.py` - 使用新配置机制

### Phase 4: 测试验证
- [ ] 编写热切换测试用例
- [ ] 验证配置变更即时生效
- [ ] 验证实例缓存正常工作
- [ ] 性能测试确保无回归

## 风险评估

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| 性能下降 | 中 | 保留指纹缓存，避免频繁重建 |
| 向后兼容 | 低 | 保留原有API，添加新功能 |
| 并发问题 | 低 | 使用线程安全的字典操作 |

## 时间估计

- Phase 1: 30分钟
- Phase 2: 1小时
- Phase 3: 2小时
- Phase 4: 1.5小时
- 总计: ~5小时
