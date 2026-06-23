from __future__ import annotations

from pathlib import Path


def detect_ci(root: Path) -> list[str]:
    ci: set[str] = set()
    if (root / ".github" / "workflows").exists():
        ci.add("github_actions")
    if (root / ".gitlab-ci.yml").exists():
        ci.add("gitlab_ci")
    if (root / ".circleci" / "config.yml").exists():
        ci.add("circleci")
    return sorted(ci)
