from __future__ import annotations

from dataclasses import dataclass

from codex_quality_gate.checks.base import CheckContext, CheckResult, passed, skipped


@dataclass(frozen=True)
class ProfileMarkerCheck:
    check_id: str
    name: str
    languages: tuple[str, ...] = ()
    frameworks: tuple[str, ...] = ()
    package_managers: tuple[str, ...] = ()
    required_files: tuple[str, ...] = ()

    def run(self, context: CheckContext) -> CheckResult:
        if self.languages and not set(self.languages).intersection(context.profile.languages):
            return skipped(self.check_id, self.name, "language marker not detected")
        if self.frameworks and not set(self.frameworks).intersection(context.profile.frameworks):
            return skipped(self.check_id, self.name, "framework marker not detected")
        if self.package_managers and not set(self.package_managers).intersection(
            context.profile.package_managers
        ):
            return skipped(self.check_id, self.name, "package manager marker not detected")
        missing = [name for name in self.required_files if not (context.root / name).exists()]
        if missing:
            return skipped(
                self.check_id, self.name, f"missing required files: {', '.join(missing)}"
            )
        return passed(self.check_id, self.name)


def default_module_check(
    check_name: str,
    *,
    languages: tuple[str, ...] = (),
    frameworks: tuple[str, ...] = (),
    package_managers: tuple[str, ...] = (),
    required_files: tuple[str, ...] = (),
) -> ProfileMarkerCheck:
    return ProfileMarkerCheck(
        check_id=check_name.replace("-", "_"),
        name=f"{check_name} module check",
        languages=languages,
        frameworks=frameworks,
        package_managers=package_managers,
        required_files=required_files,
    )
