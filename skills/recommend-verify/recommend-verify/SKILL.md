---
name: recommend-verify
description: 股票推荐票数据核验工具。每次出推荐票后，对每只票做数据比对、阈值复核、信号类型确认。确保推荐票的每项数据与本地K线数据库一致，不出现价格/均线/阈值偏差。
agent_created: true
---

# Recommend Verify — 推荐票核验流程

## 概述

每次向用户推荐股票后，必须执行以下核验流程。确保上报的每项数据与本地 `kline_cache.db` 一致，不出现价格偏差、均线错误、阈值超限等问题。

## 核验流程（每次推荐后必跑）

### 第1步：提取推荐数据

从推荐输出中，提取每只票的：
- 代码、名称
- 现价、MA5、MA10、MA20
- 均线差（MA5-MA10、MA10-MA20）
- 信号类型（缩量回踩/蓄势/放量/需观察）
- 上车条件、止损位

### 第2步：查询本地数据库

对每只票执行SQLite查询，从 `kline_cache.db` 获取实际数据：

```python
import sqlite3, numpy as np

# 查询模板
cur = conn.execute(
    'SELECT date, close, volume FROM kline_cache WHERE code=? ORDER BY date', 
    (code,)
)
rows = cur.fetchall()

closes = [r[1] for r in rows]
volumes = [r[2] for r in rows]

c = closes[-1]
ma5 = np.mean(closes[-5:])
ma10 = np.mean(closes[-10:])
ma20 = np.mean(closes[-20:])
d1 = abs(ma5-ma10)/ma10*100
d2 = abs(ma10-ma20)/ma20*100
```

### 第3步：逐项比对

对每只票输出比对结果：

| 校验项 | 用户报 | 实际 | 判定 |
|:--|:--:|:--:|:--:|
| 现价 | xx.xx | xx.xx | ✅/❌ |
| MA5 | xx.xx | xx.xx | ✅/❌ |
| MA10 | xx.xx | xx.xx | ✅/❌ |
| MA20 | xx.xx | xx.xx | ✅/❌ |
| MA5-MA10差 | x.x% | x.x% | ✅/❌(阈值2%) |
| MA10-MA20差 | x.x% | x.x% | ✅/❌(阈值4%) |

### 第4步：阈值复核

按V2.1规则判断是否真的在临界点范围内：

- MA5-MA10差 < **2%** → ✅ 临界点
- MA10-MA20差 < **4%** → ✅ 临界点
- 两者均超 → ❌ 超出临界范围，降级

### 第5步：信号类型确认

根据实际数据判断信号类型：

```python
def determine_signal(c, ma10, d1, vr):
    """按V2.1规则判断信号类型"""
    suck = vr < 0.9
    price_dev = abs(c - ma10) / ma10 * 100
    
    if suck and price_dev < 2 and d1 < 2:
        return '✅ 缩量回踩均线，最佳建仓时机，可试仓'
    elif d1 < 2 and vr > 1.2 and price_dev < 2:
        return '✅ 放量站上均线，可加仓'
    elif d1 < 2 and suck:
        return '✅ 缩量蓄势中，等待放量信号'
    else:
        return '需观察'
```

### 第6步：输出修正清单

如果发现数据偏差，给出修正后的清单：

```
修正前                          修正后
─────────────────────────────────────────────
🥇 汇顶 信号正确  ✅            保持
🥈 张江 信号正确  ✅            保持
🥉 鹏鼎 信号正确  ✅            保持
4️⃣  浪潮 信号实际为需观察 ❌    降级为观察
5️⃣  立讯 三硬伤 ❌             暂不推荐
```

## 内置阈值速查

| 指标 | 阈值 | 说明 |
|:--|:--:|:--|
| MA5-MA10差 | < **2%** | 临界点上限 |
| MA10-MA20差 | < **4%** | 临界点上限 |
| 量比(缩量) | < 0.9 | 蓄势信号 |
| 量比(放量) | > 1.2 | 突破信号 |
| 偏离MA10 | < 2% | 价格贴均线 |
| 涨停基因 | ≥1次/33天 | 有爆发记录 |
| 距前高 | > -10% | 空间充足 |
