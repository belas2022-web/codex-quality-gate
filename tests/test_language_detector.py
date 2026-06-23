from __future__ import annotations

from pathlib import Path

from codex_quality_gate.detection.language_detector import detect_languages


def test_detects_python_javascript_and_typescript(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text("[project]\nname='demo'\n", encoding="utf-8")
    (tmp_path / "package.json").write_text('{"scripts": {}}', encoding="utf-8")
    (tmp_path / "tsconfig.json").write_text("{}", encoding="utf-8")
    assert detect_languages(tmp_path) == ["javascript", "python", "typescript"]
