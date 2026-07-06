"""Tests for a_stock_quote."""

from a_stock_quote import to_tscode, parse_tencent_line


def test_to_tscode():
    assert to_tscode("600519") == "sh600519"
    assert to_tscode("000001") == "sz000001"
    assert to_tscode("sh600519") == "sh600519"


def test_parse_tencent_line():
    line = 'v_sh600519="1~贵州茅台~600519~1775.00~1760.00~1765.00~1780.00~1750.00~...~1.5~1785.00~1740.00~~~~~1234567~7890~0.85~";'
    result = parse_tencent_line(line)
    assert result is not None
    assert result["name"] == "贵州茅台"
    assert result["price"] == 1775.00
