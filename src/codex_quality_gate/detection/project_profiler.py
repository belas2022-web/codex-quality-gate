from __future__ import annotations

from pathlib import Path

from codex_quality_gate.core.result import ProjectProfile
from codex_quality_gate.detection.ci_detector import detect_ci
from codex_quality_gate.detection.framework_detector import detect_frameworks
from codex_quality_gate.detection.language_detector import detect_languages
from codex_quality_gate.detection.package_manager_detector import detect_package_managers
from codex_quality_gate.detection.risk_detector import detect_risk
from codex_quality_gate.scanner.ignore import iter_project_files

LOCKFILES = {
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "poetry.lock",
    "pdm.lock",
    "uv.lock",
    "Pipfile.lock",
    "Cargo.lock",
    "go.sum",
}
NESTED_FRONTEND_DIRS = ("frontend", "web", "app")


class ProjectProfiler:
    def profile(self, path: str | Path) -> ProjectProfile:
        root = Path(path).resolve()
        if not root.exists():
            raise FileNotFoundError(f"Project path does not exist: {root}")
        languages = detect_languages(root)
        frameworks = detect_frameworks(root)
        package_managers = detect_package_managers(root)
        ci = detect_ci(root)
        risk_profile = detect_risk(root)
        file_names = {item.name for item in iter_project_files(root)}
        frontend_package_paths = _detect_frontend_package_paths(root)
        has_tests = (root / "tests").exists() or any(
            name.startswith("test_") or name.endswith((".test.ts", ".test.js"))
            for name in file_names
        )
        has_lockfiles = bool(file_names.intersection(LOCKFILES))
        return ProjectProfile(
            root=root,
            languages=languages,
            frameworks=frameworks,
            package_managers=package_managers,
            ci=ci,
            has_tests=has_tests,
            has_lockfiles=has_lockfiles,
            risk_profile=risk_profile,
            recommended_checks=self.recommend_checks(
                languages,
                frameworks,
                risk_profile.has_updater,
                risk_profile.has_chat_bridge,
                has_frontend_packages=bool(frontend_package_paths),
            ),
            frontend_package_paths=frontend_package_paths,
        )

    def recommend_checks(
        self,
        languages: list[str],
        frameworks: list[str],
        has_updater: bool,
        has_chat_bridge: bool,
        *,
        has_frontend_packages: bool = False,
    ) -> list[str]:
        checks: set[str] = {"syntax", "custom_rules", "secrets"}
        if "python" in languages:
            checks.update({"ruff", "mypy", "pytest"})
        if {"javascript", "typescript"}.intersection(languages):
            checks.update({"eslint", "prettier", "npm_audit"})
        if "go" in languages:
            checks.update({"gofmt", "go_test"})
        if "rust" in languages:
            checks.update({"cargo_fmt", "cargo_test"})
        if "react" in frameworks or has_frontend_packages:
            checks.update({"frontend", "accessibility"})
        if has_updater:
            checks.add("updater_security")
        if has_chat_bridge:
            checks.add("chat_security")
        return sorted(checks)


def _detect_frontend_package_paths(root: Path) -> list[str]:
    paths: set[str] = set()
    for directory in NESTED_FRONTEND_DIRS:
        package_json = root / directory / "package.json"
        if package_json.exists():
            paths.add(package_json.relative_to(root).as_posix())
    packages_dir = root / "packages"
    if packages_dir.exists():
        for package_json in packages_dir.glob("*/package.json"):
            paths.add(package_json.relative_to(root).as_posix())
    return sorted(paths)
