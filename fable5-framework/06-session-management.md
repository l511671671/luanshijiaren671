# 06 会话管理（Session Management）

**目标：** 让 WorkBuddy 在多次会话之间持续工作，不丢上下文。

---

## 会话启动三问

每次启动时问自己：

1. **有没有未完成的 checkpoint？**
   - 检查 `LONG_RUN_CHECKPOINT.md`
   - 检查项目目录下的 checkpoint 文件
   - 检查最近会话日志

2. **用户上次在做什么？**
   - 读 `MEMORY.md`
   - 读 `USER.md`
   - 读项目 `AGENTS.md`

3. **今天要优先处理什么？**
   - 用户当前消息
   - 未完成的 checkpoint
   - 定期任务（如盘前推荐）

---

## Checkpoint 协议

### 何时创建 Checkpoint

- 任务预计 3 次工具调用以上且一次会话做不完
- 跨天任务
- 有明确阶段里程碑的任务

### Checkpoint 内容

```markdown
# Checkpoint: [任务名称]

**创建时间**: YYYY-MM-DD HH:MM
**预计完成时间**: YYYY-MM-DD HH:MM

## 当前阶段
[描述当前执行到哪一步]

## 下一步（恢复时第一步执行）
1. [精确的下一步操作]
2. [需要的工具/命令]

## 上下文摘要
- 用户原始需求：
- 已完成：
- 数据状态：
- 注意事项：

## 进度
[████████░░░░] 80%
```

### 何时删除 Checkpoint

任务完成后删除 `LONG_RUN_CHECKPOINT.md`，将结果归档到日志或 `MEMORY.md`。

---

## 会话交接清单

### 会话结束时
- [ ] 是否还有未完成任务？
- [ ] 是否需要写入 checkpoint？
- [ ] 是否已告知用户当前进度？
- [ ] 关键中间产物是否已保存？

### 新会话启动时
- [ ] 检查 checkpoint
- [ ] 读取 MEMORY.md / USER.md / AGENTS.md
- [ ] 向用户简要汇报恢复状态
- [ ] 确认后继续

---

## 多项目切换

如果用户在不同项目之间切换：
1. 保存当前项目的 checkpoint
2. 读取目标项目的 `AGENTS.md`
3. 确认上下文后再回答
