from __future__ import annotations

from pathlib import PurePosixPath

from codex_quality_gate.core.errors import PolicyViolationError

FORBIDDEN_PATH_PREFIXES = (".git/", ".env", "secrets/", "private_keys/", "tokens/")
REVIEW_REQUIRED_PREFIXES = (
    ".github/",
    "pyproject.toml",
    "package.json",
    "package-lock.json",
    "requirements.txt",
    "Dockerfile",
    "docker-compose.yml",
    "migrations/",
    "auth/",
    "updater/",
    "security/",
    "chat_bridge/",
)
REVIEW_REQUIRED_SEGMENTS = (
    "/auth/",
    "/updates/",
    "/updater/",
    "/security/",
    "/chat_bridge/",
    "/dashboard/",
    "/workers/",
)
TEST_PATH_PREFIXES = ("tests/", "test/")
ALLOWED_SAFE_TOOLS = {"ruff-format", "ruff-fix", "prettier", "eslint-fix", "gofmt", "cargo-fmt"}


class AutofixPolicy:
    def validate_tool(self, tool_name: str) -> None:
        if tool_name not in ALLOWED_SAFE_TOOLS:
            raise PolicyViolationError(f"Autofix tool is not allowed: {tool_name}")

    def validate_path(self, path: str) -> None:
        normalized = PurePosixPath(path.replace("\\", "/")).as_posix()
        if any(normalized.startswith(prefix) for prefix in FORBIDDEN_PATH_PREFIXES):
            raise PolicyViolationError(f"Autofix path is forbidden: {path}")

    def is_forbidden(self, path: str) -> bool:
        normalized = PurePosixPath(path.replace("\\", "/")).as_posix()
        return any(normalized.startswith(prefix) for prefix in FORBIDDEN_PATH_PREFIXES)

    def requires_review(self, path: str, change_type: str = "modified") -> bool:
        normalized = PurePosixPath(path.replace("\\", "/")).as_posix()
        if change_type in {"deleted", "removed"} and (
            normalized.startswith(TEST_PATH_PREFIXES)
            or "/tests/" in normalized
            or normalized.endswith(("_test.py", ".test.ts", ".test.js"))
        ):
            return True
        return any(normalized.startswith(prefix) for prefix in REVIEW_REQUIRED_PREFIXES) or any(
            segment in f"/{normalized}" for segment in REVIEW_REQUIRED_SEGMENTS
        )
