from __future__ import annotations

import platform


def normalized_platform(system: str | None = None, machine: str | None = None) -> str:
    sys_name = (system or platform.system()).lower()
    arch = (machine or platform.machine()).lower()
    if sys_name.startswith("win"):
        os_name = "windows"
    elif sys_name == "darwin":
        os_name = "macos"
    else:
        os_name = "linux"
    if arch in {"amd64", "x86_64"}:
        normalized_arch = "x64"
    elif arch in {"arm64", "aarch64"}:
        normalized_arch = "arm64"
    else:
        normalized_arch = arch or "unknown"
    return f"{os_name}-{normalized_arch}"
