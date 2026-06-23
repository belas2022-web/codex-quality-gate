from __future__ import annotations

from pathlib import Path

from codex_quality_gate.detection.project_profiler import ProjectProfiler


def test_detects_python_project(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        "[project]\nname='x'\ndependencies=['fastapi']\n", encoding="utf-8"
    )
    profile = ProjectProfiler().profile(tmp_path)
    assert "python" in profile.languages
    assert "fastapi" in profile.frameworks


def test_detects_node_project(tmp_path: Path) -> None:
    (tmp_path / "package.json").write_text('{"dependencies": {}}', encoding="utf-8")
    profile = ProjectProfiler().profile(tmp_path)
    assert "javascript" in profile.languages
    assert "npm" in profile.package_managers


def test_detects_typescript_project(tmp_path: Path) -> None:
    (tmp_path / "tsconfig.json").write_text("{}", encoding="utf-8")
    assert "typescript" in ProjectProfiler().profile(tmp_path).languages


def test_detects_react_vite_project(tmp_path: Path) -> None:
    (tmp_path / "package.json").write_text(
        '{"dependencies": {"react": "1", "vite": "1"}}', encoding="utf-8"
    )
    profile = ProjectProfiler().profile(tmp_path)
    assert {"react", "vite"}.issubset(set(profile.frameworks))


def test_detects_go_project(tmp_path: Path) -> None:
    (tmp_path / "go.mod").write_text("module x", encoding="utf-8")
    assert "go" in ProjectProfiler().profile(tmp_path).languages


def test_detects_rust_project(tmp_path: Path) -> None:
    (tmp_path / "Cargo.toml").write_text("[package]\nname='x'", encoding="utf-8")
    assert "rust" in ProjectProfiler().profile(tmp_path).languages


def test_detects_docker_project(tmp_path: Path) -> None:
    (tmp_path / "Dockerfile").write_text("FROM python:3.13", encoding="utf-8")
    assert ProjectProfiler().profile(tmp_path).risk_profile.has_docker


def test_detects_updater_risk(tmp_path: Path) -> None:
    (tmp_path / "updater.py").write_text("manifest = 'signature'", encoding="utf-8")
    assert ProjectProfiler().profile(tmp_path).risk_profile.has_updater


def test_detects_chat_bridge_risk(tmp_path: Path) -> None:
    (tmp_path / "slack.py").write_text("slack telegram discord teams", encoding="utf-8")
    assert ProjectProfiler().profile(tmp_path).risk_profile.has_chat_bridge


def test_recommends_checks(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text("[project]\nname='x'", encoding="utf-8")
    assert "ruff" in ProjectProfiler().profile(tmp_path).recommended_checks
