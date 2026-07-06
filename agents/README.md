# WorkBuddy 领域专家 Agent 系统

## Agent 列表

| Agent | 文件 | 触发词 | 专长 |
|-------|------|--------|------|
| Trading Agent | `trading-agent.md` | 股票、交易、买点、止损、复盘、A股 | A 股短线交易 |
| Property Agent | `property-agent.md` | 租房、租客、租金、空置、房产 | 武汉光谷房产运营 |
| Marketing Agent | `marketing-agent.md` | 营销、推广、文案、招租、活动 | 数据驱动营销 |

## 调度规则

### 1. 关键词匹配

用户 prompt 中若包含某 Agent 的核心触发词，优先交给对应 Agent。

### 2. 多 Agent 协作

| 场景 | 主 Agent | 协作 Agent |
|------|----------|------------|
| 房产招租文案 | Marketing | Property |
| 股票营销内容审核 | Marketing | Trading |
| 投资房产 vs 股票对比 | Property / Trading | 两者 |

### 3. 与 fable5-orchestrator 的关系

```
用户请求
  ↓
fable5-orchestrator 判断任务复杂度
  ↓
是否需要规划 / 多文件 / 跨会话
  ├─ 是 → 先走 fable5-orchestrator 规划流程
  ↓
是否需要领域专家
  ├─ 是 → 路由到对应 Agent
  ↓
执行 + 验证 + 交付
```

## 扩展方式

1. 在 `agents/` 目录下新增 `[domain]-agent.md`
2. 在 `orchestrator` 的 agent registry 中注册
3. 更新本 README 的 Agent 列表

## 质量要求

- 每个 Agent 必须有明确的职责边界
- 必须有触发词列表
- 必须有输出格式模板
- 必须有质量红线
