from __future__ import annotations

import json
from pathlib import Path


def test_frontend_has_dependency_free_test_script() -> None:
    package = json.loads(Path("frontend/package.json").read_text(encoding="utf-8"))

    assert package["scripts"]["test"] == "node --test test/*.test.mjs"


def test_frontend_tests_are_part_of_quality_and_release_workflows() -> None:
    for path in (".github/workflows/quality.yml", ".github/workflows/release.yml"):
        workflow = Path(path).read_text(encoding="utf-8")
        assert "npm run test" in workflow
