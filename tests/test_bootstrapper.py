from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from codex_quality_gate.installers.bootstrapper import Bootstrapper
from codex_quality_gate.installers.install_plan import InstallPlan, InstallProfile, ToolRequirement


def test_dry_run_does_not_install(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text("[project]\nname='x'", encoding="utf-8")
    plan = Bootstrapper().plan(tmp_path, InstallProfile.STANDARD, apply=False)
    assert plan.dry_run


def test_apply_requires_explicit_flag(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text("[project]\nname='x'", encoding="utf-8")
    plan = Bootstrapper().plan(tmp_path, InstallProfile.STANDARD)
    assert plan.dry_run


def test_execute_blocks_admin_or_global_installs() -> None:
    plan = InstallPlan(
        InstallProfile.STANDARD,
        dry_run=False,
        requirements=[
            ToolRequirement(
                "global-tool",
                "unsafe",
                ("python", "--version"),
                global_install=True,
            )
        ],
    )

    with pytest.raises(PermissionError, match="Unsafe install requirement blocked"):
        Bootstrapper().execute(plan)


def test_execute_reports_failed_install_command(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_run(*_args: object, **_kwargs: object) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(("python", "--bad"), 2, "", "bad flag")

    monkeypatch.setattr(subprocess, "run", fake_run)
    plan = InstallPlan(
        InstallProfile.STANDARD,
        dry_run=False,
        requirements=[ToolRequirement("python", "runtime", ("python", "--bad"))],
    )

    with pytest.raises(RuntimeError, match="bad flag"):
        Bootstrapper().execute(plan)


def test_execute_records_successful_install(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, ...]] = []

    def fake_run(
        command: tuple[str, ...],
        **_kwargs: object,
    ) -> subprocess.CompletedProcess[str]:
        calls.append(command)
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(subprocess, "run", fake_run)
    plan = InstallPlan(
        InstallProfile.STANDARD,
        dry_run=False,
        requirements=[ToolRequirement("python", "runtime", ("python", "--version"))],
    )

    assert Bootstrapper().execute(plan) == ["installed: python"]
    assert calls == [("python", "--version")]
