from __future__ import annotations

from pathlib import Path

from codex_quality_gate.core.result import ProjectProfile
from codex_quality_gate.installers.install_plan import InstallProfile
from codex_quality_gate.installers.tool_catalog import ToolCatalog


def test_tool_catalog_adds_python_and_security_tools(tmp_path: Path) -> None:
    profile = ProjectProfile(tmp_path, languages=["python"])
    plan = ToolCatalog().create_plan(profile, profile=InstallProfile.SECURITY)
    names = {requirement.name for requirement in plan.requirements}
    assert {"ruff", "mypy", "pytest", "semgrep", "bandit", "pip-audit"}.issubset(names)
    assert all(not item.global_install and not item.requires_admin for item in plan.requirements)
