from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any


class Severity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AutonomyMode(StrEnum):
    OBSERVE = "observe"
    SUGGEST = "suggest"
    AUTOFIX_SAFE = "autofix-safe"
    AUTOFIX_PR = "autofix-pr"
    MANUAL_APPROVAL = "manual-approval"


@dataclass(frozen=True)
class Finding:
    id: str
    path: str
    line: int
    column: int
    severity: Severity
    message: str
    rule_id: str
    category: str
    matched_text: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "path": self.path,
            "line": self.line,
            "column": self.column,
            "severity": self.severity.value,
            "message": self.message,
            "rule_id": self.rule_id,
            "category": self.category,
            "matched_text": self.matched_text,
        }


@dataclass(frozen=True)
class RiskProfile:
    has_updater: bool = False
    has_network: bool = False
    has_auth: bool = False
    has_database: bool = False
    has_docker: bool = False
    has_ci: bool = False
    has_chat_bridge: bool = False
    has_dashboard: bool = False
    has_secret_handling: bool = False
    has_file_writes: bool = False
    has_archive_extraction: bool = False
    has_subprocess: bool = False
    has_public_api: bool = False

    def to_dict(self) -> dict[str, bool]:
        return dict(self.__dict__)


@dataclass(frozen=True)
class ProjectProfile:
    root: Path
    languages: list[str] = field(default_factory=list)
    frameworks: list[str] = field(default_factory=list)
    package_managers: list[str] = field(default_factory=list)
    ci: list[str] = field(default_factory=list)
    has_tests: bool = False
    has_lockfiles: bool = False
    risk_profile: RiskProfile = field(default_factory=RiskProfile)
    recommended_checks: list[str] = field(default_factory=list)
    frontend_package_paths: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "root": str(self.root),
            "languages": self.languages,
            "frameworks": self.frameworks,
            "package_managers": self.package_managers,
            "ci": self.ci,
            "has_tests": self.has_tests,
            "has_lockfiles": self.has_lockfiles,
            "risk_profile": self.risk_profile.to_dict(),
            "recommended_checks": self.recommended_checks,
            "frontend_package_paths": self.frontend_package_paths,
        }


@dataclass(frozen=True)
class ScanResult:
    project: str
    profile: ProjectProfile
    findings: list[Finding]
    check_results: list[Any] = field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        return any(item.severity in {Severity.ERROR, Severity.CRITICAL} for item in self.findings)

    @property
    def has_check_failures(self) -> bool:
        failing_statuses = {"failed", "error"}
        for item in self.check_results:
            status = getattr(item, "status", "")
            value = getattr(status, "value", str(status))
            if value in failing_statuses:
                return True
        return False

    @property
    def has_policy_review(self) -> bool:
        for item in self.check_results:
            status = getattr(item, "status", "")
            value = getattr(status, "value", str(status))
            if value == "review_required":
                return True
        return False

    @property
    def has_warnings(self) -> bool:
        return any(item.severity is Severity.WARNING for item in self.findings)

    def exit_code(self, fail_on_warning: bool = False) -> int:
        if self.has_policy_review:
            return 4
        if self.has_check_failures or self.has_errors:
            return 1
        if fail_on_warning and self.has_warnings:
            return 1
        return 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "project": self.project,
            "profile": self.profile.to_dict(),
            "findings": [finding.to_dict() for finding in self.findings],
            "check_results": [
                item.to_dict() if hasattr(item, "to_dict") else item for item in self.check_results
            ],
            "summary": {
                "total": len(self.findings),
                "errors": sum(
                    finding.severity in {Severity.ERROR, Severity.CRITICAL}
                    for finding in self.findings
                ),
                "warnings": sum(finding.severity is Severity.WARNING for finding in self.findings),
                "checks": len(self.check_results),
                "failed_checks": sum(
                    getattr(getattr(item, "status", ""), "value", str(getattr(item, "status", "")))
                    in {"failed", "error"}
                    for item in self.check_results
                ),
            },
        }
