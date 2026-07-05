"""
WorkBuddy Web 工具客户端

使用 requests 发起 HTTP 请求，替代纯模拟的 web_request。
支持 GET/POST、自定义 headers、超时、重试和错误降级。
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, Optional

import requests


@dataclass
class WebResponse:
    status_code: int
    headers: Dict[str, str]
    text: str
    json_data: Optional[Dict[str, Any]] = None
    elapsed_ms: float = 0.0

    @property
    def ok(self) -> bool:
        return 200 <= self.status_code < 300

    def raise_for_status(self):
        if not self.ok:
            raise requests.HTTPError(f"HTTP {self.status_code}: {self.text[:200]}")

    def validate(self, required_status: int = 200) -> Dict[str, Any]:
        """验证响应是否满足预期。"""
        if not self.ok:
            return {"passed": False, "issues": [f"HTTP status {self.status_code}"]}
        if required_status and self.status_code != required_status:
            return {"passed": False, "issues": [f"expected status {required_status}, got {self.status_code}"]}
        if not self.text:
            return {"passed": False, "issues": ["empty response body"]}
        return {"passed": True, "issues": []}


class WebClient:
    def __init__(
        self,
        timeout: int = 30,
        retries: int = 3,
        default_headers: Optional[Dict[str, str]] = None,
    ):
        self.timeout = timeout
        self.retries = retries
        self.session = requests.Session()
        self.default_headers = default_headers or {
            "User-Agent": "WorkBuddy/1.0 (Automated Assistant)"
        }

    def get(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> WebResponse:
        return self.request("GET", url, headers=headers, params=params, **kwargs)

    def post(
        self,
        url: str,
        data: Optional[Any] = None,
        json_body: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> WebResponse:
        return self.request(
            "POST", url, data=data, json=json_body, headers=headers, **kwargs
        )

    def request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> WebResponse:
        merged_headers = {**self.default_headers, **(headers or {})}
        last_exc: Optional[Exception] = None

        for attempt in range(1, self.retries + 1):
            try:
                response = self.session.request(
                    method,
                    url,
                    headers=merged_headers,
                    timeout=self.timeout,
                    **kwargs,
                )
                return self._wrap_response(response)
            except requests.RequestException as exc:
                last_exc = exc
                if attempt == self.retries:
                    raise requests.RequestException(
                        f"{method} {url} failed after {self.retries} retries: {exc}"
                    ) from exc

        raise RuntimeError("unreachable") from last_exc

    def _wrap_response(self, response: requests.Response) -> WebResponse:
        try:
            json_data = response.json()
        except ValueError:
            json_data = None

        return WebResponse(
            status_code=response.status_code,
            headers=dict(response.headers),
            text=response.text,
            json_data=json_data,
            elapsed_ms=response.elapsed.total_seconds() * 1000,
        )


if __name__ == "__main__":
    client = WebClient()
    try:
        resp = client.get("https://httpbin.org/get")
        print(resp.status_code, resp.json_data.get("origin") if resp.json_data else None)
    except Exception as exc:
        print(f"request failed: {exc}")
