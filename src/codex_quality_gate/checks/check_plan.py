from __future__ import annotations

from dataclasses import dataclass

from codex_quality_gate.core.result import ProjectProfile

COMMON_CHECKS = ["custom_rules", "docs_check", "git_diff_policy"]
PYTHON_STANDARD_CHECKS = [
    "syntax_compile",
    "ruff_format",
    "ruff",
    "mypy",
    "pytest",
    "pytest_coverage",
]
NODE_STANDARD_CHECKS = ["npm_lint", "npm_typecheck", "npm_build", "npm_test", "npm_audit"]
SECURITY_CHECKS = ["semgrep", "bandit", "pip_audit", "updater_security", "chat_security"]
FULL_CHECKS = ["ci_check", "dependency_scan", "secrets"]

PROFILE_ORDER = {"minimal": 0, "standard": 1, "security": 2, "full": 3, "strict": 4}


@dataclass(frozen=True)
class CheckPlan:
    profile_name: str
    checks: list[str]

    def to_dict(self) -> dict[str, object]:
        return {"profile": self.profile_name, "checks": self.checks}


def build_check_plan(project_profile: ProjectProfile, profile_name: str = "standard") -> CheckPlan:
    normalized = profile_name if profile_name in PROFILE_ORDER else "standard"
    level = PROFILE_ORDER[normalized]
    checks = set(COMMON_CHECKS)
    languages = set(project_profile.languages)

    if "python" in languages:
        checks.add("syntax_compile")
    if level >= PROFILE_ORDER["standard"] and "python" in languages:
        checks.update(PYTHON_STANDARD_CHECKS)
    if level >= PROFILE_ORDER["standard"] and {"javascript", "typescript"}.intersection(languages):
        checks.update(NODE_STANDARD_CHECKS)
    if level >= PROFILE_ORDER["standard"]:
        checks.add("dependency_scan")
        checks.add("secrets")
    if level >= PROFILE_ORDER["security"]:
        checks.update(SECURITY_CHECKS)
    if level >= PROFILE_ORDER["full"]:
        checks.update(FULL_CHECKS)
    if level >= PROFILE_ORDER["strict"]:
        checks.update(SECURITY_CHECKS)

    checks.update(_normalize_recommended(project_profile.recommended_checks))
    ordered = [check for check in _stable_order() if check in checks]
    ordered.extend(sorted(checks.difference(ordered)))
    return CheckPlan(profile_name=normalized, checks=ordered)


def _normalize_recommended(checks: list[str]) -> set[str]:
    aliases = {
        "syntax": "syntax_compile",
        "format": "ruff_format",
        "lint": "ruff",
        "ruff": "ruff",
        "mypy": "mypy",
        "pytest": "pytest",
        "coverage": "pytest_coverage",
        "basic_tests": "pytest",
        "docs": "docs_check",
        "ci": "ci_check",
    }
    return {aliases.get(check, check) for check in checks}


def _stable_order() -> list[str]:
    return [
        "syntax_compile",
        "ruff_format",
        "ruff",
        "mypy",
        "pytest",
        "pytest_coverage",
        "npm_lint",
        "npm_typecheck",
        "npm_build",
        "npm_test",
        "custom_rules",
        "secrets",
        "dependency_scan",
        "git_diff_policy",
        "docs_check",
        "semgrep",
        "bandit",
        "pip_audit",
        "updater_security",
        "chat_security",
        "npm_audit",
        "ci_check",
    ]
