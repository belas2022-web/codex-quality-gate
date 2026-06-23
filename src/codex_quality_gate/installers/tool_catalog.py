from __future__ import annotations

from codex_quality_gate.core.result import ProjectProfile
from codex_quality_gate.installers.install_plan import InstallPlan, InstallProfile, ToolRequirement


class ToolCatalog:
    def requirements_for_profile(
        self, project_profile: ProjectProfile, profile: InstallProfile
    ) -> list[ToolRequirement]:
        requirements: list[ToolRequirement] = []
        if "python" in project_profile.languages:
            requirements.extend(
                [
                    ToolRequirement(
                        "packaging-toolchain",
                        "Upgrade pip, setuptools, and wheel before security auditing",
                        (
                            "python",
                            "-m",
                            "pip",
                            "install",
                            "--upgrade",
                            "pip",
                            "setuptools",
                            "wheel",
                        ),
                    ),
                    ToolRequirement(
                        "ruff", "Python lint and format", ("python", "-m", "pip", "install", "ruff")
                    ),
                    ToolRequirement(
                        "mypy", "Python type checking", ("python", "-m", "pip", "install", "mypy")
                    ),
                    ToolRequirement(
                        "pytest", "Python tests", ("python", "-m", "pip", "install", "pytest")
                    ),
                ]
            )
        if {"javascript", "typescript"}.intersection(project_profile.languages):
            requirements.append(
                ToolRequirement("npm", "Node package manager", ("node", "--version"))
            )
        if profile in {InstallProfile.SECURITY, InstallProfile.FULL, InstallProfile.STRICT}:
            requirements.extend(
                [
                    ToolRequirement(
                        "semgrep", "SAST rules", ("python", "-m", "pip", "install", "semgrep")
                    ),
                    ToolRequirement(
                        "bandit",
                        "Python security scan",
                        ("python", "-m", "pip", "install", "bandit"),
                    ),
                    ToolRequirement(
                        "pip-audit",
                        "Python dependency audit",
                        ("python", "-m", "pip", "install", "pip-audit"),
                    ),
                ]
            )
        return [
            item for item in requirements if not item.global_install and not item.requires_admin
        ]

    def create_plan(
        self,
        project_profile: ProjectProfile,
        profile: InstallProfile = InstallProfile.STANDARD,
        dry_run: bool = True,
    ) -> InstallPlan:
        return InstallPlan(
            profile=profile,
            dry_run=dry_run,
            requirements=self.requirements_for_profile(project_profile, profile),
        )
