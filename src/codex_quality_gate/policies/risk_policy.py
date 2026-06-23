from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from codex_quality_gate.core.errors import PolicyViolationError

REVIEW_REQUIRED_SEGMENTS = (
    ".github",
    "workflows",
    "updates",
    "updater",
    "update_sources",
    "security",
    "auth",
    "policies",
    "chat_bridge",
    "dashboard",
    "migrations",
    "ci",
    "release",
    "deploy",
)
REVIEW_REQUIRED_FILES = (
    "dockerfile",
    "docker-compose.yml",
    "pyproject.toml",
    "package.json",
    "package-lock.json",
    "requirements.txt",
    "requirements-dev.txt",
    "uv.lock",
    "poetry.lock",
    "pdm.lock",
    "pnpm-lock.yaml",
    "yarn.lock",
)
REVIEW_REQUIRED_PATH_PAIRS = (
    ("database", "migrations"),
    ("scripts", "release"),
)
FORBIDDEN_PATH_PREFIXES = (
    ".git",
    ".env",
    "secrets",
    "private_keys",
    "tokens",
)
TEST_DELETE_RE = re.compile(
    r"(?ms)(?:^diff --git a/(?P<path>tests?/[^ \n]+)|"
    r"^--- a/(?P<old>tests?/[^ \n]+)).*?^\+\+\+ /dev/null"
)
DISABLED_CI_RE = re.compile(r"(?i)(skip[-_ ]ci|\[ci skip\]|\bci\s*:\s*false\b)")
DISABLED_SECURITY_RE = re.compile(
    r"(?i)(disable security|security\s*:\s*false|semgrep[^\\n]*(?:skip|false|disabled)|"
    r"bandit[^\\n]*(?:skip|false|disabled)|pip-audit[^\\n]*(?:skip|false|disabled))"
)
SECRET_FILE_RE = re.compile(r"(?i)(?:id_rsa|\.pem|credentials\.json)$")


@dataclass(frozen=True)
class RiskDecision:
    blocked: bool = False
    review_required: bool = False
    reason: str = ""


class RiskPolicy:
    def validate_diff(self, diff_text: str) -> RiskDecision:
        self.block_test_deletion(diff_text)
        block_ci_disable(diff_text)
        block_security_disable(diff_text)
        self.block_secret_files(diff_text)
        if self.requires_review_for_diff(diff_text):
            return RiskDecision(
                review_required=True, reason="Sensitive path change requires review"
            )
        return RiskDecision()

    def block_test_deletion(self, diff_text: str) -> None:
        if TEST_DELETE_RE.search(diff_text) or (
            "deleted file mode" in diff_text.lower() and "/tests/" in diff_text.replace("\\", "/")
        ):
            raise PolicyViolationError("Deleting tests is blocked by policy")

    def block_secret_files(self, diff_text: str) -> None:
        for path in _diff_paths(diff_text):
            if self.is_forbidden_path(path):
                raise PolicyViolationError("Committing secret-bearing files is blocked by policy")

    def is_forbidden_path(self, path: str | Path) -> bool:
        normalized = _normalize_path(path)
        parts = _path_parts(normalized)
        if not parts:
            return False
        first = parts[0]
        if first in FORBIDDEN_PATH_PREFIXES:
            return True
        return SECRET_FILE_RE.search(normalized) is not None

    def requires_review(self, path: str | Path) -> bool:
        return self.requires_review_for_path(path)

    def requires_review_for_path(self, path: str | Path) -> bool:
        normalized = _normalize_path(path)
        parts = _path_parts(normalized)
        if not parts:
            return False
        if any(part in REVIEW_REQUIRED_SEGMENTS for part in parts):
            return True
        if parts[-1] in REVIEW_REQUIRED_FILES:
            return True
        return any(_contains_adjacent_parts(parts, pair) for pair in REVIEW_REQUIRED_PATH_PAIRS)

    def requires_review_for_diff(self, diff_text: str) -> bool:
        return any(self.requires_review_for_path(path) for path in _diff_paths(diff_text))


def block_security_disable(diff_text: str) -> None:
    if DISABLED_SECURITY_RE.search(diff_text):
        raise PolicyViolationError("Security checks cannot be disabled")


def block_ci_disable(diff_text: str) -> None:
    if DISABLED_CI_RE.search(diff_text):
        raise PolicyViolationError("CI cannot be disabled")


def _diff_paths(diff_text: str) -> list[str]:
    paths: list[str] = []
    for line in diff_text.splitlines():
        if line.startswith(("+++ b/", "--- a/")):
            path = line[6:]
            if path != "/dev/null":
                paths.append(path)
    return paths


def _normalize_path(path: str | Path) -> str:
    raw = str(path).replace("\\", "/").strip().lower()
    raw = re.sub(r"/+", "/", raw)
    while raw.startswith("./"):
        raw = raw[2:]
    return PurePosixPath(raw).as_posix().lstrip("/")


def _path_parts(path: str) -> tuple[str, ...]:
    return tuple(part for part in PurePosixPath(path).parts if part not in {"", ".", "/"})


def _contains_adjacent_parts(parts: tuple[str, ...], pair: tuple[str, str]) -> bool:
    return any(parts[index : index + len(pair)] == pair for index in range(len(parts)))
