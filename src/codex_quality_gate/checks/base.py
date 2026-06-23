from __future__ import annotations

import os
import subprocess
import sys
import time
from collections.abc import Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Protocol

from codex_quality_gate.core.result import Finding, ProjectProfile, Severity


class CheckSeverity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

    def to_finding_severity(self) -> Severity:
        return Severity(self.value)


class CheckStatus(StrEnum):
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"
    REVIEW_REQUIRED = "review_required"


@dataclass(frozen=True)
class CheckFinding:
    rule_id: str
    message: str
    path: str
    line: int = 1
    column: int = 1
    severity: CheckSeverity = CheckSeverity.ERROR
    category: str = "check"

    def to_finding(self) -> Finding:
        return Finding(
            id=f"{self.rule_id}:{self.path}:{self.line}:{self.column}",
            path=self.path,
            line=self.line,
            column=self.column,
            severity=self.severity.to_finding_severity(),
            message=self.message,
            rule_id=self.rule_id,
            category=self.category,
        )


@dataclass(frozen=True)
class CheckContext:
    root: Path
    profile: ProjectProfile
    profile_name: str = "standard"
    timeout_seconds: int = 300
    fail_on_warning: bool = False


@dataclass(frozen=True)
class CheckResult:
    check_id: str
    name: str
    status: CheckStatus
    exit_code: int
    duration_seconds: float
    command: tuple[str, ...] = ()
    stdout: str = ""
    stderr: str = ""
    findings: list[Finding] = field(default_factory=list)
    skipped_reason: str = ""

    def to_dict(self) -> dict[str, object]:
        return {
            "check_id": self.check_id,
            "name": self.name,
            "status": self.status.value,
            "exit_code": self.exit_code,
            "duration_seconds": self.duration_seconds,
            "command": list(self.command),
            "stdout": self.stdout,
            "stderr": self.stderr,
            "findings": [finding.to_dict() for finding in self.findings],
            "skipped_reason": self.skipped_reason,
        }


class BaseCheck(Protocol):
    check_id: str
    name: str

    def run(self, context: CheckContext) -> CheckResult: ...


class CommandCheck:
    def __init__(
        self,
        check_id: str,
        name: str,
        command: Sequence[str],
        *,
        required: bool = False,
        timeout_seconds: int | None = None,
    ) -> None:
        self.check_id = check_id
        self.name = name
        self.command = tuple(command)
        self.required = required
        self.timeout_seconds = timeout_seconds

    def run(self, context: CheckContext) -> CheckResult:
        if not self.command:
            return skipped(self.check_id, self.name, "empty command")
        started = time.perf_counter()
        timeout = self.timeout_seconds or context.timeout_seconds
        try:
            completed = subprocess.run(
                self.command,
                cwd=context.root,
                check=False,
                capture_output=True,
                text=True,
                timeout=timeout,
                env=_command_env(),
            )
        except FileNotFoundError:
            if self.required:
                return failed(
                    self.check_id,
                    self.name,
                    f"required tool is missing: {self.command[0]}",
                    started,
                    self.command,
                )
            return skipped(
                self.check_id,
                self.name,
                f"tool is not installed: {self.command[0]}",
                started,
                self.command,
            )
        except subprocess.TimeoutExpired as exc:
            return failed(
                self.check_id,
                self.name,
                f"check timed out after {timeout} seconds",
                started,
                self.command,
                stdout=_normalize_timeout_output(exc.stdout),
                stderr=_normalize_timeout_output(exc.stderr),
            )
        status = CheckStatus.PASSED if completed.returncode == 0 else CheckStatus.FAILED
        findings = []
        if completed.returncode != 0:
            findings.append(
                CheckFinding(
                    rule_id=self.check_id,
                    message=_first_nonempty_line(completed.stderr, completed.stdout)
                    or f"{self.name} failed",
                    path=str(context.root),
                    severity=CheckSeverity.ERROR,
                    category="check-runner",
                ).to_finding()
            )
        return CheckResult(
            check_id=self.check_id,
            name=self.name,
            status=status,
            exit_code=completed.returncode,
            duration_seconds=time.perf_counter() - started,
            command=self.command,
            stdout=completed.stdout,
            stderr=completed.stderr,
            findings=findings,
        )


def python_module_command(module: str, *args: str) -> tuple[str, ...]:
    return (sys.executable, "-m", module, *args)


def passed(
    check_id: str,
    name: str,
    *,
    started: float | None = None,
    findings: list[Finding] | None = None,
) -> CheckResult:
    return CheckResult(
        check_id=check_id,
        name=name,
        status=CheckStatus.PASSED,
        exit_code=0,
        duration_seconds=0.0 if started is None else time.perf_counter() - started,
        findings=findings or [],
    )


def skipped(
    check_id: str,
    name: str,
    reason: str,
    started: float | None = None,
    command: Sequence[str] = (),
) -> CheckResult:
    return CheckResult(
        check_id=check_id,
        name=name,
        status=CheckStatus.SKIPPED,
        exit_code=0,
        duration_seconds=0.0 if started is None else time.perf_counter() - started,
        command=tuple(command),
        skipped_reason=reason,
    )


def failed(
    check_id: str,
    name: str,
    message: str,
    started: float | None = None,
    command: Sequence[str] = (),
    *,
    stdout: str = "",
    stderr: str = "",
    status: CheckStatus = CheckStatus.FAILED,
) -> CheckResult:
    severity = (
        CheckSeverity.WARNING if status is CheckStatus.REVIEW_REQUIRED else CheckSeverity.ERROR
    )
    finding = CheckFinding(
        rule_id=check_id,
        message=message,
        path=".",
        severity=severity,
        category="check-runner",
    ).to_finding()
    return CheckResult(
        check_id=check_id,
        name=name,
        status=status,
        exit_code=1,
        duration_seconds=0.0 if started is None else time.perf_counter() - started,
        command=tuple(command),
        stdout=stdout,
        stderr=stderr,
        findings=[finding],
    )


def _first_nonempty_line(*chunks: str) -> str:
    for chunk in chunks:
        for line in chunk.splitlines():
            stripped = line.strip()
            if stripped:
                return stripped
    return ""


def _normalize_timeout_output(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode(errors="replace")
    return value


def _command_env() -> dict[str, str]:
    env = os.environ.copy()
    env.setdefault("PYTHONUTF8", "1")
    env.setdefault("PYTHONIOENCODING", "utf-8")
    return env
