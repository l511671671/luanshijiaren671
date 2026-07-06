"""Tests for tools.web_search."""

from tools import web_search as ws


class FakeResponse:
    def __init__(self, text):
        self.text = text

    def raise_for_status(self):
        pass


def test_web_search_bing(monkeypatch):
    html = """<html><body><li class="b_algo"><a href="http://example.com">Title</a><div>Body text</div></li></body></html>"""

    def fake_get(url, **kwargs):
        return FakeResponse(html)

    monkeypatch.setattr(ws.requests, "get", fake_get)
    results = ws.web_search("test", backend="bing_cn")
    assert len(results) == 1
    assert results[0]["title"] == "Title"


def test_fetch_url(monkeypatch):
    html = "<html><head><title>T</title></head><body><p>hello</p></body></html>"

    def fake_get(url, **kwargs):
        return FakeResponse(html)

    monkeypatch.setattr(ws.requests, "get", fake_get)
    result = ws.fetch_url("http://example.com")
    assert result["title"] == "T"
    assert "hello" in result["text"]
