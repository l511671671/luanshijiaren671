# WorkBuddy 长期记忆模块

基于向量存储的任务经验检索。

## 文件

- `chroma_memory.py` — ChromaDB 封装，支持 fallback

## 使用

```python
from memory import ChromaMemory

mem = ChromaMemory(persist_dir="/tmp/workbuddy_chroma")
mem.add("A 股交易规则：只买主板", {"domain": "trading"})
mem.add("房产运营：武汉光谷租金", {"domain": "property"})

results = mem.query("主板股票可以买哪些", n_results=2)
for r in results:
    print(r["text"])
```

## 依赖

```bash
pip install chromadb
```

未安装时自动降级为内存实现。
