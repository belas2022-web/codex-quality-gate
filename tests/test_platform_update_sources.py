from __future__ import annotations

from codex_quality_gate.core.platform import normalized_platform
from codex_quality_gate.update_sources.github_releases import GitHubReleasesSource


def test_platform_detects_windows_x64() -> None:
    assert normalized_platform("Windows", "AMD64") == "windows-x64"


def test_platform_detects_linux_x64() -> None:
    assert normalized_platform("Linux", "x86_64") == "linux-x64"


def test_platform_detects_macos_arm64() -> None:
    assert normalized_platform("Darwin", "arm64") == "macos-arm64"


def test_platform_uses_unknown_arch_fallback() -> None:
    assert normalized_platform("Linux", "riscv64") == "linux-riscv64"


def test_github_releases_endpoint() -> None:
    source = GitHubReleasesSource("owner/repo")
    assert source.repository == "owner/repo"
