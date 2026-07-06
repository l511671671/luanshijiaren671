# WorkBuddy 多 Agent 协作模块

Planner + Executor + MessageQueue 基础实现，未来可替换为 Redis/RabbitMQ。

## 组件

- `message_queue.py` — 内存消息队列
- `planner.py` — 任务规划 Agent
- `executor.py` — 任务执行 Agent
- `orchestrator.py` — 总调度器

## 使用

```python
from multi_agent import MultiAgentOrchestrator

orchestrator = MultiAgentOrchestrator()

handlers = {
    "analyze": lambda step: "analyzed",
    "implement": lambda step: "implemented",
}

result = orchestrator.run("帮我写一个 Python 脚本", handlers=handlers)
print(result["plan"])
print(result["results"])
```

## 测试

```bash
python test_new_modules.py
```
