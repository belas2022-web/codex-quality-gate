from __future__ import annotations

import json

from codex_quality_gate.updates.update_client import UpdateClient


class Response:
    def __init__(self, payload: dict[str, object]) -> None:
        self.payload = payload
        self.content = json.dumps(payload).encode()
        self.headers: dict[str, str] = {"Content-Length": str(len(self.content))}
        self.status_code = 200
        self.url = str(payload["url"])

    def json(self) -> dict[str, object]:
        return self.payload

    def raise_for_status(self) -> None:
        return None

    def iter_content(self, chunk_size: int = 65536):
        _ = chunk_size
        yield self.content


class Session:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def get(self, url: str, **kwargs: object) -> Response:
        self.calls.append({"url": url, **kwargs})
        return Response({"url": url, "timeout": kwargs["timeout"]})


def test_update_client_uses_timeout_for_json_and_bytes() -> None:
    session = Session()
    client = UpdateClient(session, timeout=7.0)  # type: ignore[arg-type]
    assert client.get_json("https://good.example/latest.json")["timeout"] == 7.0
    assert json.loads(client.get_bytes("https://good.example/rules.json"))["url"] == (
        "https://good.example/rules.json"
    )
    assert session.calls == [
        {
            "url": "https://good.example/latest.json",
            "timeout": 7.0,
            "allow_redirects": False,
            "stream": True,
        },
        {
            "url": "https://good.example/rules.json",
            "timeout": 7.0,
            "allow_redirects": False,
            "stream": True,
        },
    ]
