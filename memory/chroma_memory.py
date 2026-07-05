"""
WorkBuddy 长期记忆向量存储

使用 ChromaDB 保存任务经验，支持：
- 添加经验（文本 + 元数据）
- 根据查询文本检索相似经验
- 失败时回退到内存字典

如果 ChromaDB 未安装，则使用纯内存实现。
"""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

try:
    import chromadb
    from chromadb.config import Settings

    HAS_CHROMA = True
except ImportError:  # pragma: no cover
    HAS_CHROMA = False

try:
    from sentence_transformers import SentenceTransformer

    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:  # pragma: no cover
    HAS_SENTENCE_TRANSFORMERS = False


@dataclass
class MemoryEntry:
    id: str
    text: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class SimpleEmbeddingFunction:
    """轻量级 embedding，无需外部模型。仅用于 fallback。"""

    def __init__(self):
        self._word_index: Dict[str, int] = {}

    def _tokenize(self, text: str) -> List[str]:
        return re.findall(r"[\w\u4e00-\u9fff]+", text.lower())

    def _vector(self, text: str) -> List[float]:
        tokens = self._tokenize(text)
        vector = defaultdict(float)
        for token in tokens:
            idx = self._word_index.setdefault(token, len(self._word_index))
            vector[idx] += 1.0
        if not vector:
            return []
        dim = max(self._word_index.values()) + 1
        return [vector[i] for i in range(dim)]

    def __call__(self, texts: List[str]) -> List[List[float]]:
        return [self._vector(t) for t in texts]


def cosine_similarity(a: List[float], b: List[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(x * x for x in b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


class SentenceTransformerEmbedding:
    """sentence-transformers 封装，支持本地缓存。"""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)

    def __call__(self, texts: List[str]) -> List[List[float]]:
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        return [list(e) for e in embeddings]


class ChromaMemory:
    def __init__(self, collection_name: str = "workbuddy_memory", persist_dir: Optional[str] = None):
        self.collection_name = collection_name
        self.persist_dir = persist_dir
        self._memory_store: Dict[str, MemoryEntry] = {}

        if HAS_SENTENCE_TRANSFORMERS:
            try:
                self._embedder = SentenceTransformerEmbedding()
            except Exception:
                self._embedder = SimpleEmbeddingFunction()
        else:
            self._embedder = SimpleEmbeddingFunction()

        if HAS_CHROMA:
            try:
                client_settings = Settings(
                    chroma_db_impl="duckdb+parquet",
                    persist_directory=persist_dir or "/tmp/workbuddy_chroma",
                )
                self._client = chromadb.Client(client_settings)
                self._collection = self._client.get_or_create_collection(
                    name=collection_name,
                    embedding_function=None,
                )
            except Exception:
                self._client = None
                self._collection = None
        else:
            self._client = None
            self._collection = None

    def add(self, text: str, metadata: Optional[Dict[str, Any]] = None, entry_id: Optional[str] = None) -> str:
        metadata = metadata or {}
        entry_id = entry_id or str(len(self._memory_store))
        entry = MemoryEntry(id=entry_id, text=text, metadata=metadata)
        self._memory_store[entry_id] = entry

        if self._collection is not None:
            try:
                self._collection.add(
                    ids=[entry_id],
                    documents=[text],
                    metadatas=[metadata],
                )
            except Exception:
                pass
        return entry_id

    def query(self, text: str, n_results: int = 3) -> List[Dict[str, Any]]:
        if self._collection is not None:
            try:
                results = self._collection.query(
                    query_texts=[text],
                    n_results=n_results,
                )
                return [
                    {
                        "id": results["ids"][0][i],
                        "text": results["documents"][0][i],
                        "metadata": results["metadatas"][0][i],
                        "distance": results["distances"][0][i],
                    }
                    for i in range(len(results["ids"][0]))
                ]
            except Exception:
                pass

        return self._fallback_query(text, n_results)

    def _fallback_query(self, text: str, n_results: int) -> List[Dict[str, Any]]:
        query_vec = self._embedder._vector(text)
        scored = []
        for entry_id, entry in self._memory_store.items():
            entry_vec = self._embedder._vector(entry.text)
            sim = cosine_similarity(query_vec, entry_vec)
            scored.append((sim, entry_id, entry))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [
            {
                "id": entry_id,
                "text": entry.text,
                "metadata": entry.metadata,
                "score": score,
            }
            for score, entry_id, entry in scored[:n_results]
        ]


if __name__ == "__main__":
    mem = ChromaMemory()
    mem.add("A 股交易规则：只买主板，回避创业板", {"domain": "trading"})
    mem.add("房产运营：武汉光谷租金参考", {"domain": "property"})
    print(mem.query("主板股票可以买哪些"))
