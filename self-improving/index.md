# Self-Improving Index

WorkBuddy 的自进化中心。所有错误、模式、改进点都归档在这里。

## Files

| File | Purpose | Update Trigger |
|------|---------|----------------|
| `corrections.md` | 已纠正的错误记录 | 每次犯错/被纠正后 |
| `patterns.md` | 高频模式与最佳实践 | 发现可复用模式时 |
| `review-template.md` | 周期性复盘模板 | 每周/每月复盘 |
| `memory.md` | 自改进相关的记忆摘要 | 长期记忆更新时 |

## Fable 5 能力框架

WorkBuddy 持续向 Fable 5 靠拢，核心框架见 `fable5-framework/`：

| 文件 | 能力 |
|------|------|
| `01-planning.md` | 任务规划与拆解 |
| `02-reasoning.md` | 深度推理与方案对比 |
| `03-execution.md` | 执行纪律与工具使用 |
| `04-verification.md` | 多层验证体系 |
| `05-error-recovery.md` | 错误诊断与恢复 |
| `06-session-management.md` | 会话启动、续接、收尾 |
| `07-quality-gates.md` | 质量门与 Definition of Done |

## Workflow

1. **发生错误** → 立即写入 `corrections.md`
2. **发现模式** → 提炼后写入 `patterns.md`
3. **周期复盘** → 使用 `review-template.md` 检查进度
4. **能力进化** → 按 Fable 5 框架复盘交付过程
5. **沉淀到记忆** → 重要的长期教训更新到 `MEMORY.md`

## Quality Rule

宁可多花 30% 时间验证，也不交付未经验证的结果。

## 进化目标

| 目标 | 当前状态 | 下一步 |
|------|:--------:|:------|
| 规划前必做方案对比 | 🔄 | 每次复杂任务都生成 plan |
| 边做边验证 | 🔄 | 每个子任务都有验证动作 |
| 跨会话续接 | 🔄 | 长任务自动写 checkpoint |
| 错误归档率 | 🔄 | 每次错误都写入 corrections |
| 首次交付成功率 | 🔄 | 通过质量门后再交付 |
