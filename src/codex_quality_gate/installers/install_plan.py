from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class InstallProfile(StrEnum):
    MINIMAL = "minimal"
    STANDARD = "standard"
    SECURITY = "security"
    FULL = "full"
    STRICT = "strict"


@dataclass(frozen=True)
class ToolRequirement:
    name: str
    purpose: str
    install_command: tuple[str, ...]
    global_install: bool = False
    requires_admin: bool = False


@dataclass(frozen=True)
class InstallPlan:
    profile: InstallProfile
    dry_run: bool = True
    requirements: list[ToolRequirement] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "profile": self.profile.value,
            "dry_run": self.dry_run,
            "requirements": [
                {
                    "name": item.name,
                    "purpose": item.purpose,
                    "install_command": list(item.install_command),
                    "global_install": item.global_install,
                    "requires_admin": item.requires_admin,
                }
                for item in self.requirements
            ],
        }
