# Fable 5+ 级能力框架

**Version:** 2026-07-05
**Goal:** 让 WorkBuddy 的交付纪律、推理深度、任务持续性和错误恢复能力不仅达到 Fable 5，更通过工程化补充超越 Fable 5 的固有限制。

---

## Fable 5 的核心特征

1. **先想清楚，再动手** — 执行前完成方案对比、边界分析、失败预判
2. **边做边验证** — 每完成一个子任务都验证，不是等最后一起检查
3. **跨会话持续** — 长任务能断点续传，不丢失上下文
4. **自动纠错** — 遇到错误能快速定位、隔离、恢复
5. **交付即正确** — 第一次就把事做对，宁可慢，不要返工

---

## WorkBuddy 对 Fable 5 的超越点

| 能力 | Fable 5 现状 | WorkBuddy 增强 |
|------|--------------|----------------|
| 模型选择 | 单一模型，无 fallback | 多模型路由 + fallback 链 (`router/model_router.py`) |
| 领域专业性 | 通用 Agent | 交易 / 房产 / 营销 专家 Agent (`agents/`) |
| 成本控制 | 所有任务用同一模型 | 四级 Tier 按需路由 (`MODEL-STRATEGY.md`) |
| 长期记忆 | 基于文本记忆 | 记忆 + 模式 + 复盘三线沉淀 (`self-improving/`) |
| 工程集成 | 框架为主 | 可运行的路由模块 + 测试用例 |

---

## 本框架目录

| 文件 | 能力 |
|------|------|
| `01-planning.md` | 任务规划与拆解 |
| `02-reasoning.md` | 深度推理与方案对比 |
| `03-execution.md` | 执行纪律与工具使用 |
| `04-verification.md` | 多层验证体系 |
| `05-error-recovery.md` | 错误诊断与恢复 |
| `06-session-management.md` | 会话启动、续接、收尾 |
| `07-quality-gates.md` | 质量门与 Definition of Done |

---

## 使用方式

### 每次接到复杂任务时
1. 打开 `02-reasoning.md`，先完成推理
2. 打开 `01-planning.md`，拆出执行计划
3. 执行过程中参考 `03-execution.md`
4. 每个子任务完成后按 `04-verification.md` 验证
5. 最终按 `07-quality-gates.md` 验收

### 任务中断/跨会话时
- 使用 `06-session-management.md` 写入 checkpoint
- 新会话先读取 checkpoint

### 遇到错误时
- 使用 `05-error-recovery.md` 定位和恢复
- 将错误写入 `self-improving/corrections.md`

---

## 与现有技能的关系

| 现有技能 | 对应框架 |
|----------|----------|
| `deep-reason` | `02-reasoning.md` |
| `self-validate` | `04-verification.md` + `07-quality-gates.md` |
| `long-horizon` | `06-session-management.md` |
| `fable5-orchestrator`（新增） | 整体调度，触发上述流程 |
