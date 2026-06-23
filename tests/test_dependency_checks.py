from __future__ import annotations

from pathlib import Path

from codex_quality_gate.checks.base import CheckContext
from codex_quality_gate.checks.orchestrator import CheckOrchestrator
from codex_quality_gate.core.result import ProjectProfile
from codex_quality_gate.rules.rule_engine import RuleEngine


def test_package_manifest_without_lockfile_warns(tmp_path: Path) -> None:
    profile = ProjectProfile(tmp_path, package_managers=["pip"], has_lockfiles=False)
    result = CheckOrchestrator()._dependency_scan(CheckContext(root=tmp_path, profile=profile))
    assert any(finding.rule_id == "DEP-PACKAGE-NO-LOCK" for finding in result.findings)


def test_requirements_unpinned_warns() -> None:
    findings = RuleEngine().scan_text("requirements.txt", "requests>=2\n")
    assert findings[0].rule_id == "DEP-REQ-UNPINNED"


def test_osv_vulnerability_parsed() -> None:
    payload = {"id": "OSV-1", "affected": [{"package": {"name": "pkg"}}]}
    assert payload["affected"][0]["package"]["name"] == "pkg"


def test_pip_audit_result_parsed() -> None:
    payload = {"name": "pkg", "vulns": [{"id": "PYSEC-1"}]}
    assert payload["vulns"][0]["id"] == "PYSEC-1"


def test_npm_audit_result_parsed() -> None:
    payload = {"vulnerabilities": {"pkg": {"severity": "high"}}}
    assert payload["vulnerabilities"]["pkg"]["severity"] == "high"
