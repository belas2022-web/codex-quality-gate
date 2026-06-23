from __future__ import annotations


def available_checks() -> list[str]:
    return [
        "syntax",
        "format",
        "lint",
        "typecheck",
        "tests",
        "coverage",
        "custom_rules",
        "secrets",
        "dependency_scan",
        "git_diff_policy",
        "updater_security",
        "chat_security",
    ]
