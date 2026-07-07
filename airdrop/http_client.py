"""Small requests wrapper with sane defaults for collectors."""

from __future__ import annotations

from typing import Any
import requests

DEFAULT_HEADERS = {
    "User-Agent": "FreaktoAirdropRadar/1.0 (+https://github.com/) Python requests",
    "Accept": "application/json,text/plain,*/*",
}


class HttpClient:
    def __init__(self, timeout: int = 20, headers: dict[str, str] | None = None):
        self.timeout = timeout
        self.headers = {**DEFAULT_HEADERS, **(headers or {})}

    def get_json(self, url: str, params: dict[str, Any] | None = None) -> Any:
        response = requests.get(url, params=params, headers=self.headers, timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    def get_text(self, url: str, params: dict[str, Any] | None = None) -> str:
        response = requests.get(url, params=params, headers=self.headers, timeout=self.timeout)
        response.raise_for_status()
        return response.text
