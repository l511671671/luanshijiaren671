---
name: long-horizon
description: "对标 Fable 5 数天自主运行能力。将跨会话的长程任务拆分为 checkpoint，每次会话结束时写入进度，下次会话从 checkpoint 恢复。触发词：跨会话、需要多次运行、长期任务、分段执行、checkpoint、续接、continue、resume。"
agent_created: true
---

# 长程任务断点续传 — Fable 5 级持续性

## 核心原则

**每次会话结束时，留有状态让下一次启动的我只需 1 分钟就能接上。** Fable 5 能在 agent harness 里跑数天——我做不到，但我能通过 checkpoint 协议让跨会话工作不停顿。

## Checkpoint 协议

### 启动检查（每会话第一步）
在开始工作前，检查项目中是否存在 `LONG_RUN_CHECKPOINT.md` 或搜索最新日志中的 `[CHECKPOINT]` 标记：
- 存在 → 先恢复上下文，继续未完成的工作
- 不存在 → 新任务，正常开始

### 任务规模判定
判定当前任务是否需要 checkpoint：
- 预计需要**3+ 次工具调用**且**无法在一次会话内完成** → 创建 checkpoint
- 跨天任务 → 必须创建 checkpoint
- 单次会话内能完成的 → 不创建 checkpoint，避免噪音

### Checkpoint 写入（每会话结束前）
写入项目根目录 `LONG_RUN_CHECKPOINT.md`：

```markdown
# 长程任务 Checkpoint — [任务名称]
**创建时间**: YYYY-MM-DD HH:MM
**预计完成时间**: YYYY-MM-DD HH:MM

## 当前阶段
[描述当前执行到哪一步]

## 下一步（恢复时第一步执行）
1. [精确的下一步操作]
2. [需要的工具/命令]

## 上下文摘要
- 用户原始需求：[一句话]
- 已完成：[关键里程碑]
- 数据状态：[文件/数据库路径]
- 注意事项：[踩过的坑/特殊配置]

## 进度
[████████░░░░] 80%
```

### 会话恢复（新会话第一步）
1. 读取所有日志文件（最近 3 天）
2. 读取 `LONG_RUN_CHECKPOINT.md`（如存在）
3. 读取 `.workbuddy/memory/MEMORY.md`
4. 向用户报告恢复状态，确认后继续

## 何时删除 Checkpoint
任务完全完成后，删除 `LONG_RUN_CHECKPOINT.md`，将结果归档到日志。

## 与 Self-Validate 的协作
每个 checkpoint 阶段结束时，必须通过 self-validate 的验证清单后才能标记该阶段完成。
