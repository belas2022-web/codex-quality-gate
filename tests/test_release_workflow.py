from __future__ import annotations

from pathlib import Path


def test_release_workflow_is_autonomous_for_release_candidates() -> None:
    workflow = Path(".github/workflows/release.yml").read_text(encoding="utf-8")

    assert "workflow_dispatch:" in workflow
    assert "tags:" in workflow
    assert "v*" in workflow
    assert 'python -m pip install -e ".[dev]"' in workflow
    assert "python -m ruff check ." in workflow
    assert "python -m ruff format --check ." in workflow
    assert "python -m mypy ." in workflow
    assert "python -m pytest --cov" in workflow
    assert "python -m codex_quality_gate check-catalogs" in workflow
    assert "codex-quality-gate check . --fail-on-warning" in workflow
    assert "codex-quality-gate check . --profile security --json" in workflow
    assert "codex-quality-gate check . --profile full --json" in workflow
    assert "npm ci" in workflow
    assert "npm run lint" in workflow
    assert "npm run typecheck" in workflow
    assert "npm run test" in workflow
    assert "npm run build" in workflow
    assert "npm audit --audit-level=high" in workflow
    assert "python -m build" in workflow
    assert "dist/rules.json" in workflow
    assert "dist/semgrep.yml" in workflow
    assert "python -m codex_quality_gate.release_automation" in workflow
    assert "codex-quality-gate --version" in workflow
    assert "codex-quality-gate doctor" in workflow
    assert "codex-quality-gate check-catalogs" in workflow
    assert "actions/upload-artifact" in workflow
    assert "softprops/action-gh-release" in workflow
    assert "RELEASE_ED25519_PRIVATE_KEY_B64" in workflow
    assert "dist/SHA256SUMS" in workflow
    assert "dist/latest.json" in workflow


def test_workflows_force_utf8_for_python_tooling() -> None:
    for path in (".github/workflows/quality.yml", ".github/workflows/release.yml"):
        workflow = Path(path).read_text(encoding="utf-8")
        assert 'PYTHONUTF8: "1"' in workflow
        assert "PYTHONIOENCODING: utf-8" in workflow
