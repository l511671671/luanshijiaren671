"""
真实网页搜索

支持 Bing 中国站和 DuckDuckGo HTML，作为 python-agent-web-search skill 的可执行落地。

用法：
    from tools.web_search import web_search
    results = web_search("A股 实时行情")
"""

from __future__ import annotations

import random
import re
import urllib.parse
from typing import Dict, List, Optional

import requests
from bs4 import BeautifulSoup


DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/125.0 Safari/537.36"
    )
}


def _fetch(url: str, timeout: int = 15) -> requests.Response:
    return requests.get(url, headers=DEFAULT_HEADERS, timeout=timeout)


def search_bing_cn(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    """搜索 cn.bing.com，解析结果列表。"""
    encoded = urllib.parse.quote(query)
    url = f"https://cn.bing.com/search?q={encoded}&setmkt=zh-CN&setlang=zh-CN"
    try:
        resp = _fetch(url)
        resp.raise_for_status()
    except Exception as exc:
        return [{"title": "error", "href": "", "body": str(exc)}]

    soup = BeautifulSoup(resp.text, "html.parser")
    results = []
    for li in soup.select("li.b_algo"):
        a = li.find("a")
        if not a:
            continue
        title = a.get_text(strip=True)
        href = a.get("href", "")
        body = li.get_text(" ", strip=True).replace(title, "", 1).strip()
        results.append({"title": title, "href": href, "body": body[:200]})
        if len(results) >= max_results:
            break
    return results


def search_duckduckgo_html(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    """搜索 DuckDuckGo HTML 端点。"""
    encoded = urllib.parse.quote(query)
    url = f"https://html.duckduckgo.com/html/?q={encoded}"
    try:
        resp = _fetch(url)
        resp.raise_for_status()
    except Exception as exc:
        return [{"title": "error", "href": "", "body": str(exc)}]

    soup = BeautifulSoup(resp.text, "html.parser")
    results = []
    for result in soup.select(".result"):
        a = result.find("a", class_="result__a")
        if not a:
            continue
        title = a.get_text(strip=True)
        href = a.get("href", "")
        snippet = result.find("a", class_="result__snippet")
        body = snippet.get_text(strip=True) if snippet else ""
        results.append({"title": title, "href": href, "body": body[:200]})
        if len(results) >= max_results:
            break
    return results


def web_search(query: str, backend: str = "auto", max_results: int = 5) -> List[Dict[str, str]]:
    """
    网页搜索入口。
    backend: auto | bing_cn | duckduckgo
    """
    if backend == "auto":
        # 中文查询优先 Bing 中国
        backend = "bing_cn" if any("\u4e00" <= c <= "\u9fff" for c in query) else "duckduckgo"

    if backend == "bing_cn":
        return search_bing_cn(query, max_results)
    return search_duckduckgo_html(query, max_results)


def fetch_url(url: str, timeout: int = 20) -> Dict[str, str]:
    """抓取网页并返回清洗后的正文。"""
    try:
        resp = _fetch(url, timeout=timeout)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "header", "footer", "aside"]):
            tag.decompose()
        title = soup.title.get_text(strip=True) if soup.title else ""
        text = soup.get_text("\n", strip=True)
        # 简单去重空行
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        return {"title": title, "url": url, "text": "\n".join(lines[:2000])}
    except Exception as exc:
        return {"title": "error", "url": url, "text": str(exc)}


if __name__ == "__main__":
    import json
    import sys

    q = sys.argv[1] if len(sys.argv) > 1 else "A股 实时行情"
    print(json.dumps(web_search(q), ensure_ascii=False, indent=2))
