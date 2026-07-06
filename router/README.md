# WorkBuddy 多模型路由模块

基于 `MODEL-STRATEGY.md` 实现的多模型路由与 fallback 机制。

## 功能

- **任务分级**：将用户请求自动分为 4 个 Tier
  - Tier 1 轻量：摘要、翻译、格式化
  - Tier 2 标准：代码/文档/脚本生成
  - Tier 3 复杂：架构、方案、多文件、跨会话任务
  - Tier 4 验证：复核、检查、回归、审计
- **模型选择**：根据 Tier 选择最合适的主模型
- **Fallback 链**：主模型失败时，按策略切换到备用模型
- **失败模型跳过**：支持记录已失败的模型，避免重复尝试

## 文件

- `model_router.py`：核心路由逻辑
- `test_model_router.py`：测试用例
- `README.md`：使用说明

## 快速开始

### 1. 独立运行示例

```bash
python router/model_router.py "帮我设计一个A股量化交易系统"
```

### 2. 在代码中使用

```python
from router.model_router import ModelRouter

router = ModelRouter()
result = router.route("帮我设计一个A股量化交易系统")
print(result.selected.id)  # deepseek-v4
print(result.tier)         # TaskTier.TIER_3_COMPLEX
print([m.id for m in result.fallback_chain])
```

### 3. 运行测试

```bash
python router/test_model_router.py
```

## 扩展模型池

```python
from router.model_router import ModelRouter, ModelConfig

models = [
    ModelConfig(id="gpt-4o", name="GPT-4o", vendor="OpenAI", tier="complex"),
    ModelConfig(id="claude-3-5", name="Claude 3.5", vendor="Anthropic", tier="verify"),
]
router = ModelRouter(models=models)
```

## 集成到 WorkBuddy

1. 在 WorkBuddy 主程序中导入 `ModelRouter`
2. 用户发送请求时调用 `router.route(prompt)`
3. 使用 `result.selected` 作为目标模型
4. 模型调用失败时，从 `result.fallback_chain` 取下一个模型重试
5. 将失败模型 id 传入 `route_with_fallback` 避免重复尝试
