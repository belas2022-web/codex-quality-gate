from __future__ import annotations

from pathlib import Path

from codex_quality_gate.detection.project_profiler import ProjectProfiler
from codex_quality_gate.installers.install_plan import InstallProfile
from codex_quality_gate.installers.tool_catalog import ToolCatalog


def _profile(tmp_path: Path):
    (tmp_path / "pyproject.toml").write_text("[project]\nname='x'", encoding="utf-8")
    return ProjectProfiler().profile(tmp_path)


def test_creates_minimal_install_plan(tmp_path: Path) -> None:
    plan = ToolCatalog().create_plan(_profile(tmp_path), InstallProfile.MINIMAL)
    assert plan.profile is InstallProfile.MINIMAL


def test_creates_standard_install_plan(tmp_path: Path) -> None:
    plan = ToolCatalog().create_plan(_profile(tmp_path), InstallProfile.STANDARD)
    assert any(item.name == "ruff" for item in plan.requirements)


def test_creates_security_install_plan(tmp_path: Path) -> None:
    plan = ToolCatalog().create_plan(_profile(tmp_path), InstallProfile.SECURITY)
    assert any(item.name == "semgrep" for item in plan.requirements)


def test_creates_full_install_plan(tmp_path: Path) -> None:
    plan = ToolCatalog().create_plan(_profile(tmp_path), InstallProfile.FULL)
    assert any(item.name == "pip-audit" for item in plan.requirements)


def test_no_admin_install(tmp_path: Path) -> None:
    plan = ToolCatalog().create_plan(_profile(tmp_path), InstallProfile.SECURITY)
    assert all(not item.requires_admin for item in plan.requirements)


def test_no_global_install_by_default(tmp_path: Path) -> None:
    plan = ToolCatalog().create_plan(_profile(tmp_path), InstallProfile.SECURITY)
    assert all(not item.global_install for item in plan.requirements)
