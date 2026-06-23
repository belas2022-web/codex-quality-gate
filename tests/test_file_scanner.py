from __future__ import annotations

from pathlib import Path

from codex_quality_gate.scanner.file_scanner import FileScanner


def test_ignores_node_modules(tmp_path: Path) -> None:
    path = tmp_path / "node_modules" / "x.py"
    path.parent.mkdir()
    path.write_text("print('x')", encoding="utf-8")
    assert FileScanner().scan(tmp_path) == []


def test_ignores_git(tmp_path: Path) -> None:
    path = tmp_path / ".git" / "x.py"
    path.parent.mkdir()
    path.write_text("print('x')", encoding="utf-8")
    assert FileScanner().scan(tmp_path) == []


def test_handles_bad_utf8(tmp_path: Path) -> None:
    path = tmp_path / "x.py"
    path.write_bytes(b"abc\xff")
    assert FileScanner().scan(tmp_path)[0].text


def test_skips_large_file(tmp_path: Path) -> None:
    path = tmp_path / "x.py"
    path.write_text("a" * 20, encoding="utf-8")
    assert FileScanner(max_bytes=5).scan(tmp_path) == []


def test_finds_line_column(tmp_path: Path) -> None:
    path = tmp_path / "x.py"
    path.write_text("a\nvalue = eval(x)", encoding="utf-8")
    from codex_quality_gate.rules.rule_engine import RuleEngine

    finding = RuleEngine().scan_text(path, path.read_text(encoding="utf-8"))[0]
    assert finding.line == 2
    assert finding.column == 9


def test_respects_extensions(tmp_path: Path) -> None:
    (tmp_path / "x.md").write_text("eval(x)", encoding="utf-8")
    assert FileScanner().scan(tmp_path) == []
