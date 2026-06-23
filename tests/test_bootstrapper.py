from __future__ import annotations

from pathlib import Path

from codex_quality_gate.installers.bootstrapper import Bootstrapper
from codex_quality_gate.installers.install_plan import InstallProfile


def test_dry_run_does_not_install(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text("[project]\nname='x'", encoding="utf-8")
    plan = Bootstrapper().plan(tmp_path, InstallProfile.STANDARD, apply=False)
    assert plan.dry_run


def test_apply_requires_explicit_flag(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text("[project]\nname='x'", encoding="utf-8")
    plan = Bootstrapper().plan(tmp_path, InstallProfile.STANDARD)
    assert plan.dry_run
