from __future__ import annotations

import importlib
import pkgutil
from datetime import UTC, datetime
from pathlib import Path

import pytest

import codex_quality_gate.checks as checks_package
from codex_quality_gate.checks.base import CheckContext, CheckStatus
from codex_quality_gate.checks.orchestrator import CheckOrchestrator
from codex_quality_gate.core.errors import PolicyViolationError, SecurityVerificationError
from codex_quality_gate.core.result import ProjectProfile
from codex_quality_gate.policies.risk_policy import RiskPolicy
from codex_quality_gate.updates.security import (
    reject_expired_manifest,
    reject_replay_manifest,
    safe_join,
    validate_file_size,
)


def test_all_check_modules_expose_runnable_factories(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("readme", encoding="utf-8")
    (tmp_path / "Dockerfile").write_text("FROM scratch\n", encoding="utf-8")
    workflow = tmp_path / ".github" / "workflows"
    workflow.mkdir(parents=True)
    (workflow / "quality.yml").write_text("name: quality\n", encoding="utf-8")
    profile = ProjectProfile(
        tmp_path,
        languages=["python", "javascript", "typescript", "go", "rust", "java", "dotnet"],
        frameworks=["react"],
        package_managers=["pip", "npm", "go", "cargo", "maven", "gradle", "dotnet"],
    )
    context = CheckContext(root=tmp_path, profile=profile)
    package_path = Path(checks_package.__file__).parent
    modules = [
        item.name
        for item in pkgutil.iter_modules([str(package_path)])
        if item.name.endswith("_checks")
    ]
    assert modules
    for module_name in modules:
        module = importlib.import_module(f"codex_quality_gate.checks.{module_name}")
        checks = module.create_checks()
        assert checks[0].run(context).status in {CheckStatus.PASSED, CheckStatus.SKIPPED}


def test_orchestrator_missing_tool_ci_and_npm_branches(tmp_path: Path) -> None:
    orchestrator = CheckOrchestrator()
    context = CheckContext(root=tmp_path, profile=ProjectProfile(tmp_path))
    assert (
        orchestrator._python_module_runner(
            context, "missing_optional", "missing optional", "missing_optional_mod", ()
        ).status
        is CheckStatus.SKIPPED
    )
    assert (
        orchestrator._python_module_runner(
            context,
            "missing_required",
            "missing required",
            "missing_required_mod",
            (),
            required=True,
        ).status
        is CheckStatus.FAILED
    )
    assert orchestrator._npm_runner(context, "npm_lint").status is CheckStatus.SKIPPED
    ci_missing = orchestrator._ci_check(context)
    assert ci_missing.findings[0].rule_id == "CI-QUALITY-GATE-MISSING"

    workflow = tmp_path / ".github" / "workflows"
    workflow.mkdir(parents=True)
    (workflow / "quality.yml").write_text("name: quality\n", encoding="utf-8")
    ci_failed = orchestrator._ci_check(context)
    assert ci_failed.status is CheckStatus.FAILED


def test_policy_review_and_secret_file_branches() -> None:
    policy = RiskPolicy()
    decision = policy.validate_diff("+++ b/.github/workflows/quality.yml\n+name: quality\n")
    assert decision.review_required
    with pytest.raises(PolicyViolationError):
        policy.validate_diff("+++ b/.env\n+TOKEN=x\n")


def test_update_security_negative_branches(tmp_path: Path) -> None:
    with pytest.raises(SecurityVerificationError):
        validate_file_size(-1, 10)
    with pytest.raises(SecurityVerificationError):
        reject_replay_manifest({}, [])
    with pytest.raises(SecurityVerificationError):
        reject_expired_manifest({"expires_at": "not-a-date"})
    with pytest.raises(SecurityVerificationError):
        reject_expired_manifest(
            {"expires_at": "2099-01-01T00:00:00Z"},
            now=datetime(2100, 1, 1, tzinfo=UTC),
        )
    with pytest.raises(SecurityVerificationError):
        safe_join(tmp_path, tmp_path / "absolute.json")
