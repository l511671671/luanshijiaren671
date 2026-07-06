---
name: python-agent-web-search
description: This skill should be used when a Python-based agent or chatbot needs real-time web search capabilities. It provides a multi-backend search tool, web page fetching, and search-augmented answer generation that can be integrated into model routers and CLI interfaces.
agent_created: true
---

# Python Agent Web Search

## Overview

This skill adds real-time web search to a Python agent or chatbot without requiring paid API keys. It supports multiple search backends and automatically decides whether a user query needs fresh internet information before answering.

## When to Use

Use this skill when:
- A user asks for real-time information such as weather, stock prices, news, sports scores, or current events.
- The agent's base model cannot answer because its knowledge is outdated.
- The project is a Python-based agent with a model router and CLI or chat interface.

## Core Capabilities

### 1. Multi-Backend Web Search

Create a `WebSearchTool` class that supports several backends:

- `bing_cn`: Parses `cn.bing.com` search results. Often the most stable in Chinese network environments.
- `duckduckgo`: Uses the `duckduckgo-search` library (free, no API key). Best when DuckDuckGo/Bing is reachable.
- `baidu`: Parses `m.baidu.com` search results. Useful fallback, but may trigger CAPTCHA under heavy use.
- `duckduckgo_html`: Parses the DuckDuckGo HTML endpoint as a minimal-dependency fallback.

Key implementation points:
- Use `httpx` for HTTP requests and `BeautifulSoup` for HTML parsing.
- Auto backend selection: prefer `bing_cn` for Chinese queries and DuckDuckGo for others.
- Return structured results with `title`, `href`, and `body` fields.
- Handle CAPTCHA redirects gracefully by returning empty results so the next backend can be tried.

Example class layout:

```python
class WebSearchTool(BaseTool):
    def execute(self, query, max_results=5, backend="auto", region="cn-zh", fetch_content=False) -> ToolResult:
        ...
```

### 2. Web Page Fetching

Create a `WebFetchTool` class that:
- Fetches a URL using `httpx` with a desktop user-agent.
- Removes noise tags (`script`, `style`, `nav`, `header`, `footer`, `aside`, etc.).
- Extracts main content from semantic tags (`article`, `main`, `[role='main']`, `.content`).
- Returns cleaned text with title, URL, and optional links.

### 3. Search-Augmented Answer Generation

Create a `WebSearchAssistant` class that:
- Detects whether a query needs real-time search via keyword matching.
- Runs the search when needed.
- Optionally fetches the top result pages for richer context.
- Builds a prompt like:

```
You are a helpful assistant. Answer based on the following real-time web search results.
If the results lack relevant information, say so. Do not make up facts.

<search results>

User question: <query>
```
- Sends the combined prompt to the model router and returns the model name and answer.

Detection keywords should cover:
- Weather: 天气, 气温, 下雨, 下雪, 台风, 预报, weather, forecast
- Time/Current events: 今天, 现在, 当前, 实时, 最新, 刚刚, today, current, latest
- Finance: 股价, 股票, 行情, 大盘, 指数, 基金, 净值, 汇率, stock price, price, rate
- News/Hot topics: 新闻, 热点, 热搜, 事件, 消息, news, hot
- Sports: 比分, 比赛结果, 赛程, 排名, score, live
- General lookup phrases: 帮我查, 查一下, 查询, 是多少, 怎么样

### 4. Router Integration

Extend the model router with a `route_with_search()` method. The router stores the full config so it can read search settings from `tools.search`:

```python
async def route_with_search(self, prompt: str, intent: dict = None) -> tuple[str, str]:
    if self._search_assistant is None:
        from ..tools.search_integration import WebSearchAssistant
        search_cfg = self._full_config.get("tools", {}).get("search", {})
        self._search_assistant = WebSearchAssistant(
            model_router=self,
            max_results=search_cfg.get("max_results", 5),
            auto_fetch=search_cfg.get("auto_fetch", True),
            max_context_chars=search_cfg.get("max_context_chars", 6000),
            backend=search_cfg.get("backend", "auto"),
        )
    return await self._search_assistant.answer(prompt, intent=intent)
```

### 5. CLI / Chat Integration

In the chat command handler, route normal user questions through `route_with_search` instead of `route`, so weather/news/price queries automatically trigger search.

```python
model, reply = await router.route_with_search(user_input)
```

Keep explicit task commands (`run`, `reason`, `team`, `long`) on the normal engine pipeline.

## Configuration

Add a `search` section under `tools` in the agent config file:

```yaml
tools:
  search:
    enabled: true
    backend: "auto"          # auto | bing_cn | duckduckgo | baidu | duckduckgo_html
    max_results: 5
    auto_fetch: true         # whether to fetch top result pages
    max_context_chars: 6000  # context window for search results
    region: "cn-zh"          # DuckDuckGo region
```

## Dependencies

Add to `requirements.txt`:

```
httpx>=0.27
beautifulsoup4>=4.12
duckduckgo-search>=5.0
```

## Testing

Add a verification test that checks:
- Intent detection (weather query triggers search; general chat does not).
- Search result formatting.
- A live search returns at least one result (with a try/except to skip on network failure).

Prefer using `backend="auto"` in tests so the most available backend for the current network is used automatically.

## Design Notes

- Do not search for sensitive queries (passwords, keys, IDs, personal privacy).
- If all backends fail, fall back to the model with a note that search was unavailable.
- Keep search results concise to avoid exceeding the model's context window.
- If a backend returns CAPTCHA or a redirect to a verification page, return empty results and let the caller try the next backend.
