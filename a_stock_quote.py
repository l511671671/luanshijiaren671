"""
A股实时行情查询（腾讯 qt.gtimg.cn）

用法：
    from a_stock_quote import get_batch_quotes
    print(get_batch_quotes(["sh600519", "sz000001"]))
"""

from __future__ import annotations

from typing import Dict, List, Optional

import requests


_TENCENT_URL = "http://qt.gtimg.cn/q="


class StockQuoteError(Exception):
    pass


def to_tscode(code: str) -> str:
    """6 位代码前补 sh/sz。"""
    code = code.strip().lower()
    if code.startswith(("sh", "sz")):
        return code
    if code.startswith("6"):
        return f"sh{code}"
    return f"sz{code}"


def parse_tencent_line(line: str) -> Optional[Dict]:
    if ";" not in line:
        return None
    line = line.strip().rstrip(";")
    if "=" not in line:
        return None
    symbol_part, data = line.split("=", 1)
    code = symbol_part.split("_")[-1]
    fields = [f.strip('"') for f in data.split("~")]
    # fields[0]=name, [2]=price, [4]=close, [5]=open, [32]=change%, [33]=high, [34]=low, [38]=turnover
    if len(fields) < 39:
        return None
    try:
        price = float(fields[2])
        close = float(fields[4]) if fields[4] else None
        change_pct = float(fields[32]) if fields[32] else None
        high = float(fields[33]) if fields[33] else None
        low = float(fields[34]) if fields[34] else None
        turnover = float(fields[38]) if fields[38] else None
    except ValueError:
        price = close = change_pct = high = low = turnover = None
    return {
        "code": code,
        "name": fields[0] if fields else "",
        "price": price,
        "close": close,
        "open": float(fields[5]) if len(fields) > 5 and fields[5] else None,
        "change_pct": change_pct,
        "high": high,
        "low": low,
        "turnover": turnover,
    }


def get_batch_quotes(codes: List[str]) -> List[Dict]:
    if not codes:
        return []
    tscodes = [to_tscode(c) for c in codes]
    url = _TENCENT_URL + ",".join(tscodes)
    try:
        resp = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        resp.encoding = "gbk"
    except Exception as exc:
        raise StockQuoteError(f"请求行情失败: {exc}")

    results = []
    for line in resp.text.split("\n"):
        line = line.strip()
        if not line:
            continue
        quote = parse_tencent_line(line)
        if quote:
            results.append(quote)
    return results


def get_index_quotes() -> List[Dict]:
    return get_batch_quotes(["sh000001", "sz399001", "sh000300"])
