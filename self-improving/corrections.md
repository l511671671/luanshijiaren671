# Corrections Log

记录 WorkBuddy 犯过的错误和修正方案。每条记录应包括：
- 问题描述
- 错误原因
- 正确做法
- 预防措施
- 状态

## Correction Template

```
### DATE-NNN: 简短标题
- **问题**: 
- **根因**: 
- **修正**: 
- **预防**: 
- **状态**: ✅ Fixed / 🔄 In Progress
```

---

### 2026-06-21-001: wxa-skills-generate 命令名拼写错误
- **问题**: 搜索技能时使用了错误的命令名 `wxa-skill-generate`
- **根因**: 漏掉了 `skills` 中的 `s`
- **修正**: 正确命令为 `wxa-skills-generate`
- **预防**: 不确定命令时先 `skillhub search` 或查看帮助
- **状态**: ✅ Fixed

### 2026-06-21-002: 同花顺 SelfStockCache.json 格式误判
- **问题**: 错误猜测了 `SelfStockCache.json` 的字段结构
- **根因**: 没有先读取实际文件就假设了格式
- **修正**: 实际格式是 `codes|,|flags`，字段名为 `StatusCode` / `StatusMsg` / `Data`
- **预防**: 处理任何文件前先 `Read` 确认结构
- **状态**: ✅ Fixed

### 2026-06-21-003: 东财 push2 价格单位误判
- **问题**: 以为东财 push2 数据是虚假的
- **根因**: 不知道价格单位是 "分"，需除以 100 转为元
- **修正**: 读取后 `/100` 转换
- **预防**: 新数据源先用已知标的手动校验单位和量纲
- **状态**: ✅ Fixed
