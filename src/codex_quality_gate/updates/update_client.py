from __future__ import annotations

import json
from dataclasses import dataclass
from hashlib import sha256
from typing import Any
from urllib.parse import urljoin

import requests

from codex_quality_gate.constants import DEFAULT_TIMEOUT_SECONDS
from codex_quality_gate.core.errors import SecurityVerificationError
from codex_quality_gate.updates.security import (
    validate_file_size,
    validate_https_url,
    validate_no_redirect_to_untrusted_domain,
    validate_update_url,
)

DEFAULT_MAX_UPDATE_BYTES = 5 * 1024 * 1024
REDIRECT_STATUS_CODES = {301, 302, 303, 307, 308}


@dataclass(frozen=True)
class UpdateFetchResult:
    original_url: str
    final_url: str
    redirect_chain: tuple[str, ...]
    content_length: int | None
    content: bytes
    sha256: str


class UpdateClient:
    def __init__(
        self, session: requests.Session | None = None, timeout: float = DEFAULT_TIMEOUT_SECONDS
    ) -> None:
        self.session = session or requests.Session()
        self.timeout = timeout

    def get_json(
        self,
        url: str,
        *,
        allowed_domains: list[str] | None = None,
        max_size_bytes: int = DEFAULT_MAX_UPDATE_BYTES,
    ) -> dict[str, Any]:
        result = self.fetch(url, allowed_domains=allowed_domains, max_size_bytes=max_size_bytes)
        payload = json.loads(result.content.decode("utf-8"))
        if not isinstance(payload, dict):
            raise TypeError("Expected JSON object")
        return payload

    def get_bytes(
        self,
        url: str,
        *,
        allowed_domains: list[str] | None = None,
        max_size_bytes: int = DEFAULT_MAX_UPDATE_BYTES,
    ) -> bytes:
        return self.fetch(
            url,
            allowed_domains=allowed_domains,
            max_size_bytes=max_size_bytes,
        ).content

    def fetch(
        self,
        url: str,
        *,
        allowed_domains: list[str] | None = None,
        max_size_bytes: int = DEFAULT_MAX_UPDATE_BYTES,
        max_redirects: int = 5,
    ) -> UpdateFetchResult:
        original_url = url
        current_url = url
        redirect_chain: list[str] = []
        _validate_url(current_url, allowed_domains)
        for _redirect_count in range(max_redirects + 1):
            response = self.session.get(
                current_url,
                timeout=self.timeout,
                allow_redirects=False,
                stream=True,
            )
            status_code = int(getattr(response, "status_code", 200))
            if status_code in REDIRECT_STATUS_CODES:
                headers = getattr(response, "headers", {})
                location = headers.get("Location", "")
                if not location:
                    raise SecurityVerificationError("Update redirect response is missing Location")
                next_url = urljoin(current_url, location)
                _validate_redirect(current_url, next_url, allowed_domains)
                redirect_chain.append(next_url)
                current_url = next_url
                continue

            final_url = str(getattr(response, "url", current_url) or current_url)
            _validate_redirect(current_url, final_url, allowed_domains)
            headers = getattr(response, "headers", {})
            content_length = _content_length(headers.get("Content-Length"))
            if content_length is not None:
                validate_file_size(content_length, max_size_bytes)
            response.raise_for_status()
            content = _read_limited(response, max_size_bytes)
            return UpdateFetchResult(
                original_url=original_url,
                final_url=final_url,
                redirect_chain=tuple(redirect_chain),
                content_length=content_length,
                content=content,
                sha256=sha256(content).hexdigest(),
            )
        raise SecurityVerificationError(f"Update redirect chain exceeded {max_redirects} redirects")


def _validate_url(url: str, allowed_domains: list[str] | None) -> None:
    if allowed_domains is None:
        validate_https_url(url)
        return
    validate_update_url(url, allowed_domains)


def _validate_redirect(
    current_url: str,
    final_url: str,
    allowed_domains: list[str] | None,
) -> None:
    if allowed_domains is None:
        validate_https_url(final_url)
        return
    validate_no_redirect_to_untrusted_domain(current_url, final_url, allowed_domains)


def _content_length(raw: str | None) -> int | None:
    if raw in (None, ""):
        return None
    try:
        return int(str(raw))
    except ValueError as exc:
        raise SecurityVerificationError(f"Invalid update Content-Length: {raw}") from exc


def _read_limited(response: requests.Response, max_size_bytes: int) -> bytes:
    if not hasattr(response, "iter_content"):
        content = getattr(response, "content", b"")
        validate_file_size(len(content), max_size_bytes)
        return bytes(content)
    chunks: list[bytes] = []
    total = 0
    for chunk in response.iter_content(chunk_size=65536):
        if not chunk:
            continue
        total += len(chunk)
        validate_file_size(total, max_size_bytes)
        chunks.append(chunk)
    return b"".join(chunks)
