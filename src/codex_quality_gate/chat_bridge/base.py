from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

import requests

from codex_quality_gate.constants import DEFAULT_TIMEOUT_SECONDS


@dataclass(frozen=True)
class ChatMessage:
    connector: str
    source_id: str
    author: str
    text: str


class ChatConnector(Protocol):
    name: str

    def list_messages(self, source_id: str) -> list[ChatMessage]: ...

    def send_report(self, target_id: str, text: str) -> dict[str, Any]: ...


class HttpTransport:
    def __init__(
        self, session: requests.Session | None = None, timeout: float = DEFAULT_TIMEOUT_SECONDS
    ) -> None:
        self.session = session or requests.Session()
        self.timeout = timeout

    def get(self, url: str, **kwargs: Any) -> requests.Response:
        return self.session.get(url, timeout=self.timeout, **kwargs)

    def post(self, url: str, **kwargs: Any) -> requests.Response:
        return self.session.post(url, timeout=self.timeout, **kwargs)
