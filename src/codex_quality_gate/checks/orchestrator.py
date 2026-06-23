from __future__ import annotations

import importlib.util
import json
import py_compile
import re
import shutil
import subprocess
import time
from pathlib import Path

from codex_quality_gate.checks.base import (
    CheckContext,
    CheckFinding,
    CheckResult,
    CheckSeverity,
    CheckStatus,
    CommandCheck,
    failed,
    passed,
    python_module_command,
    skipped,
)
from codex_quality_gate.checks.check_plan import build_check_plan
from codex_quality_gate.core.errors import PolicyViolationError
from codex_quality_gate.core.result import Finding, ScanResult, Severity
from codex_quality_gate.detection.project_profiler import ProjectProfiler
from codex_quality_gate.rules.rule_engine import RuleEngine
from codex_quality_gate.scanner.file_scanner import FileScanner, SourceFile

SEMGREP_CONFIG = Path(__file__).resolve().parents[1] / "data" / "default_semgrep.yml"
SECRET_ASSIGNMENT_RE = re.compile(
    r"(?i)\b(?:password|api[_-]?key|secret|token)\s*[:=]\s*[\"'][^\"']{12,}[\"']"
)


class CheckOrchestrator:
    def __init__(
        self,
        profiler: ProjectProfiler | None = None,
        scanner: FileScanner | None = None,
        rule_engine: RuleEngine | None = None,
        timeout_seconds: int = 300,
    ) -> None:
        self.profiler = profiler or ProjectProfiler()
        self.scanner = scanner or FileScanner()
        self.rule_engine = rule_engine or RuleEngine()
        self.timeout_seconds = timeout_seconds

    def run(
        self,
        path: str | Path,
        profile_name: str = "standard",
        *,
        fail_on_warning: bool = False,
    ) -> ScanResult:
        profile = self.profiler.profile(path)
        plan = build_check_plan(profile, profile_name)
        context = CheckContext(
            root=profile.root,
            profile=profile,
            profile_name=plan.profile_name,
            timeout_seconds=self.timeout_seconds,
            fail_on_warning=fail_on_warning,
        )
        sources = self.scanner.scan(profile.root)
        check_results = [self._run_check(check_id, context, sources) for check_id in plan.checks]
        findings: list[Finding] = []
        for result in check_results:
            findings.extend(result.findings)
        return ScanResult(
            project=profile.root.name,
            profile=profile,
            findings=findings,
            check_results=check_results,
        )

    def _run_check(
        self,
        check_id: str,
        context: CheckContext,
        sources: list[SourceFile],
    ) -> CheckResult:
        required_security = context.profile_name in {"security", "full", "strict"}
        if check_id == "syntax_compile":
            return self._syntax_compile(context, sources)
        if check_id == "custom_rules":
            return self._custom_rules(context, sources)
        if check_id == "docs_check":
            return self._docs_check(context)
        if check_id == "git_diff_policy":
            return self._git_diff_policy(context)
        if check_id == "dependency_scan":
            return self._dependency_scan(context)
        if check_id == "secrets":
            return self._secrets_check(context, sources)
        if check_id == "ci_check":
            return self._ci_check(context)
        if check_id == "updater_security":
            return self._risk_marker_check(
                context,
                "updater_security",
                "Updater security",
                context.profile.risk_profile.has_updater,
            )
        if check_id == "chat_security":
            return self._risk_marker_check(
                context,
                "chat_security",
                "ChatBridge security",
                context.profile.risk_profile.has_chat_bridge,
            )
        if check_id == "ruff_format":
            return self._python_module_runner(
                context,
                check_id,
                "ruff format",
                "ruff",
                ("format", "--check", "."),
            )
        if check_id == "ruff":
            return self._python_module_runner(
                context,
                check_id,
                "ruff lint",
                "ruff",
                ("check", "."),
            )
        if check_id == "mypy":
            return self._python_module_runner(context, check_id, "mypy", "mypy", (".",))
        if check_id == "pytest":
            return self._python_module_runner(context, check_id, "pytest", "pytest", ("-q",))
        if check_id == "pytest_coverage":
            return self._python_module_runner(
                context,
                check_id,
                "pytest coverage",
                "pytest",
                ("--cov", "-q"),
            )
        if check_id == "bandit":
            return self._python_module_runner(
                context,
                check_id,
                "bandit",
                "bandit",
                ("-q", "-r", "src", "-ll"),
                required=required_security,
            )
        if check_id == "pip_audit":
            return self._python_module_runner(
                context,
                check_id,
                "pip-audit",
                "pip_audit",
                (".", "--skip-editable"),
                required=required_security,
            )
        if check_id == "semgrep":
            return self._command_runner(
                context,
                check_id,
                "semgrep",
                resolve_tool_command(
                    context.root,
                    "semgrep",
                    "semgrep",
                    "--config",
                    str(SEMGREP_CONFIG),
                    "--quiet",
                    ".",
                ),
                required=required_security,
            )
        if check_id.startswith("npm_"):
            return self._npm_runner(context, check_id)
        return skipped(check_id, check_id.replace("_", " ").title(), "no runner registered")

    def _syntax_compile(self, _context: CheckContext, sources: list[SourceFile]) -> CheckResult:
        started = time.perf_counter()
        findings: list[Finding] = []
        for source in sources:
            if source.path.suffix != ".py":
                continue
            try:
                py_compile.compile(str(source.path), doraise=True)
            except py_compile.PyCompileError as exc:
                findings.append(
                    CheckFinding(
                        rule_id="syntax_compile",
                        message=str(exc.msg),
                        path=str(source.path),
                        severity=CheckSeverity.ERROR,
                        category="syntax",
                    ).to_finding()
                )
        status = CheckStatus.FAILED if findings else CheckStatus.PASSED
        return CheckResult(
            check_id="syntax_compile",
            name="Python syntax compile",
            status=status,
            exit_code=1 if findings else 0,
            duration_seconds=time.perf_counter() - started,
            findings=findings,
        )

    def _custom_rules(self, _context: CheckContext, sources: list[SourceFile]) -> CheckResult:
        started = time.perf_counter()
        findings: list[Finding] = []
        for source in sources:
            findings.extend(self.rule_engine.scan_text(source.path, source.text))
        has_error = any(item.severity in {Severity.ERROR, Severity.CRITICAL} for item in findings)
        return CheckResult(
            check_id="custom_rules",
            name="Built-in custom rules",
            status=CheckStatus.FAILED if has_error else CheckStatus.PASSED,
            exit_code=1 if has_error else 0,
            duration_seconds=time.perf_counter() - started,
            findings=findings,
        )

    def _docs_check(self, context: CheckContext) -> CheckResult:
        started = time.perf_counter()
        findings = [
            CheckFinding(
                rule_id=f"DOC-MISSING-{name.removesuffix('.md').upper()}",
                message=f"{name} is missing.",
                path=str(context.root / name),
                severity=CheckSeverity.WARNING,
                category="docs",
            ).to_finding()
            for name in ("README.md", "SECURITY.md", "CHANGELOG.md")
            if not (context.root / name).exists()
        ]
        return CheckResult(
            check_id="docs_check",
            name="Documentation files",
            status=CheckStatus.PASSED,
            exit_code=0,
            duration_seconds=time.perf_counter() - started,
            findings=findings,
        )

    def _git_diff_policy(self, context: CheckContext) -> CheckResult:
        if not (context.root / ".git").exists():
            return skipped("git_diff_policy", "Git diff policy", "not a git repository")
        started = time.perf_counter()
        completed = subprocess.run(
            ("git", "diff", "--no-ext-diff"),
            cwd=context.root,
            check=False,
            capture_output=True,
            text=True,
            timeout=context.timeout_seconds,
        )
        if completed.returncode != 0:
            return failed(
                "git_diff_policy",
                "Git diff policy",
                completed.stderr.strip() or "git diff failed",
                started,
                ("git", "diff", "--no-ext-diff"),
                stdout=completed.stdout,
                stderr=completed.stderr,
            )
        try:
            from codex_quality_gate.policies.risk_policy import RiskPolicy

            decision = RiskPolicy().validate_diff(completed.stdout)
        except PolicyViolationError as exc:
            return failed(
                "git_diff_policy",
                "Git diff policy",
                str(exc),
                started,
                ("git", "diff", "--no-ext-diff"),
                stdout=completed.stdout,
                status=CheckStatus.REVIEW_REQUIRED,
            )
        if decision.review_required:
            return failed(
                "git_diff_policy",
                "Git diff policy",
                decision.reason,
                started,
                ("git", "diff", "--no-ext-diff"),
                stdout=completed.stdout,
                status=CheckStatus.REVIEW_REQUIRED,
            )
        return passed("git_diff_policy", "Git diff policy", started=started)

    def _dependency_scan(self, context: CheckContext) -> CheckResult:
        if not context.profile.package_managers:
            return skipped("dependency_scan", "Dependency scan", "no dependency manifest detected")
        findings: list[Finding] = []
        if not context.profile.has_lockfiles:
            findings.append(
                CheckFinding(
                    rule_id="DEP-PACKAGE-NO-LOCK",
                    message="Dependency manifest is present without a detected lockfile.",
                    path=str(context.root),
                    severity=CheckSeverity.WARNING,
                    category="dependency",
                ).to_finding()
            )
        return CheckResult(
            check_id="dependency_scan",
            name="Dependency manifest scan",
            status=CheckStatus.PASSED,
            exit_code=0,
            duration_seconds=0.0,
            findings=findings,
        )

    def _secrets_check(self, _context: CheckContext, sources: list[SourceFile]) -> CheckResult:
        findings: list[Finding] = []
        for source in sources:
            for match in SECRET_ASSIGNMENT_RE.finditer(source.text):
                line = source.text.count("\n", 0, match.start()) + 1
                line_start = source.text.rfind("\n", 0, match.start()) + 1
                findings.append(
                    CheckFinding(
                        rule_id="CFG-SECRET-IN-CONFIG",
                        message="Potential secret-like assignment found.",
                        path=str(source.path),
                        line=line,
                        column=match.start() - line_start + 1,
                        severity=CheckSeverity.WARNING,
                        category="secrets",
                    ).to_finding()
                )
        return CheckResult(
            check_id="secrets",
            name="Secret marker scan",
            status=CheckStatus.PASSED,
            exit_code=0,
            duration_seconds=0.0,
            findings=findings,
        )

    def _ci_check(self, context: CheckContext) -> CheckResult:
        workflow = context.root / ".github" / "workflows" / "quality.yml"
        if not workflow.exists():
            return CheckResult(
                check_id="ci_check",
                name="CI quality workflow",
                status=CheckStatus.PASSED,
                exit_code=0,
                duration_seconds=0.0,
                findings=[
                    CheckFinding(
                        rule_id="CI-QUALITY-GATE-MISSING",
                        message="Quality workflow is missing.",
                        path=str(workflow),
                        severity=CheckSeverity.WARNING,
                        category="ci",
                    ).to_finding()
                ],
            )
        text = workflow.read_text(encoding="utf-8", errors="replace")
        findings: list[Finding] = []
        if "default_semgrep.yml" not in text:
            findings.append(
                CheckFinding(
                    rule_id="AI-SECURITY-SCAN-DISABLE",
                    message="CI does not reference default_semgrep.yml.",
                    path=str(workflow),
                    severity=CheckSeverity.ERROR,
                    category="ci",
                ).to_finding()
            )
        if "check-catalogs" not in text:
            findings.append(
                CheckFinding(
                    rule_id="CI-QUALITY-GATE-MISSING",
                    message="CI does not validate built-in catalogs.",
                    path=str(workflow),
                    severity=CheckSeverity.WARNING,
                    category="ci",
                ).to_finding()
            )
        has_error = any(item.severity in {Severity.ERROR, Severity.CRITICAL} for item in findings)
        return CheckResult(
            check_id="ci_check",
            name="CI quality workflow",
            status=CheckStatus.FAILED if has_error else CheckStatus.PASSED,
            exit_code=1 if has_error else 0,
            duration_seconds=0.0,
            findings=findings,
        )

    def _risk_marker_check(
        self,
        _context: CheckContext,
        check_id: str,
        name: str,
        risk_present: bool,
    ) -> CheckResult:
        if not risk_present:
            return skipped(check_id, name, "project risk marker not detected")
        return passed(check_id, name)

    def _python_module_runner(
        self,
        context: CheckContext,
        check_id: str,
        name: str,
        module: str,
        args: tuple[str, ...],
        *,
        required: bool = False,
    ) -> CheckResult:
        if importlib.util.find_spec(module) is None:
            if required:
                return failed(check_id, name, f"required Python module is missing: {module}")
            return skipped(check_id, name, f"Python module is not installed: {module}")
        return self._command_runner(
            context,
            check_id,
            name,
            python_module_command(module, *args),
            required=required,
        )

    def _command_runner(
        self,
        context: CheckContext,
        check_id: str,
        name: str,
        command: tuple[str, ...],
        *,
        required: bool = False,
    ) -> CheckResult:
        return CommandCheck(check_id, name, command, required=required).run(context)

    def _npm_runner(self, context: CheckContext, check_id: str) -> CheckResult:
        package_json = _npm_package_json(context)
        if package_json is None:
            return skipped(check_id, check_id.replace("_", " "), "package.json is missing")
        run_context = _context_for_package(context, package_json)
        scripts = _read_package_scripts(package_json)
        script_name = {
            "npm_lint": "lint",
            "npm_typecheck": "typecheck",
            "npm_build": "build",
            "npm_test": "test",
        }.get(check_id)
        npm = _npm_executable()
        if check_id == "npm_audit":
            return self._command_runner(
                run_context, check_id, "npm audit", (npm, "audit", "--json")
            )
        if script_name is None:
            return skipped(check_id, check_id.replace("_", " "), "unknown npm runner")
        if script_name not in scripts:
            return skipped(check_id, f"npm {script_name}", f"npm script is missing: {script_name}")
        return self._command_runner(
            run_context,
            check_id,
            f"npm {script_name}",
            (npm, "run", script_name, "--if-present"),
        )


def _read_package_scripts(package_json: Path) -> dict[str, str]:
    try:
        payload = json.loads(package_json.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    scripts = payload.get("scripts", {})
    return scripts if isinstance(scripts, dict) else {}


def _npm_package_json(context: CheckContext) -> Path | None:
    root_package = context.root / "package.json"
    if root_package.exists():
        return root_package
    for relative in context.profile.frontend_package_paths:
        package_json = context.root / relative
        if package_json.exists() and package_json.name == "package.json":
            return package_json
    return None


def _context_for_package(context: CheckContext, package_json: Path) -> CheckContext:
    package_root = package_json.parent
    if package_root == context.root:
        return context
    return CheckContext(
        root=package_root,
        profile=context.profile,
        profile_name=context.profile_name,
        timeout_seconds=context.timeout_seconds,
        fail_on_warning=context.fail_on_warning,
    )


def _npm_executable() -> str:
    return shutil.which("npm") or shutil.which("npm.cmd") or "npm"


def resolve_tool_command(
    root: Path,
    executable: str,
    module: str,
    *args: str,
) -> tuple[str, ...]:
    path_tool = shutil.which(executable)
    if path_tool:
        return (path_tool, *args)

    candidates = [
        root / ".venv" / "Scripts" / f"{executable}.exe",
        root / ".venv" / "Scripts" / executable,
        root / ".venv" / "bin" / executable,
    ]
    for candidate in candidates:
        if candidate.exists():
            return (str(candidate), *args)

    if importlib.util.find_spec(module) is not None:
        return python_module_command(module, *args)
    return (executable, *args)
