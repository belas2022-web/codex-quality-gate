from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"
BACKEND_ENTRY = ROOT / "tools" / "desktop_dashboard_api.py"
BACKEND_DIST = FRONTEND / "desktop-backend"
PACKAGE_OUTPUT = FRONTEND / "dist-desktop"
PYINSTALLER_WORK = ROOT / "build" / "pyinstaller"
PYINSTALLER_COMMAND_LABEL = "pyinstaller"


def resolve_command(name: str) -> str:
    local_name = f"{name}.cmd" if os.name == "nt" else name
    local_command = FRONTEND / "node_modules" / ".bin" / local_name
    if local_command.exists():
        return str(local_command)
    discovered = shutil.which(local_name) or shutil.which(name)
    if discovered:
        return discovered
    raise SystemExit(f"missing command: {name}")


def run(command: list[str], cwd: Path) -> None:
    subprocess.run(command, cwd=cwd, check=True, shell=False)


def remove_generated_path(path: Path) -> None:
    if not path.exists():
        return
    frontend_root = FRONTEND.resolve()
    resolved = path.resolve()
    if frontend_root != resolved and frontend_root not in resolved.parents:
        raise SystemExit(f"refusing to remove generated path outside frontend: {resolved}")
    if path.is_dir():
        shutil.rmtree(path)
    else:
        path.unlink()


def clean_package_output() -> None:
    remove_generated_path(PACKAGE_OUTPUT / "win-unpacked")
    remove_generated_path(PACKAGE_OUTPUT / "win-unpacked.tmp")
    if PACKAGE_OUTPUT.exists():
        for artifact in PACKAGE_OUTPUT.glob("*.nsis.7z"):
            remove_generated_path(artifact)


def build_backend() -> None:
    BACKEND_DIST.mkdir(parents=True, exist_ok=True)
    PYINSTALLER_WORK.mkdir(parents=True, exist_ok=True)
    run(
        [
            sys.executable,
            "-m",
            "PyInstaller",
            "--clean",
            "--noconfirm",
            "--onefile",
            "--name",
            "cqg-dashboard-api",
            "--distpath",
            str(BACKEND_DIST),
            "--workpath",
            str(PYINSTALLER_WORK),
            "--specpath",
            str(PYINSTALLER_WORK),
            "--collect-data",
            "codex_quality_gate",
            str(BACKEND_ENTRY),
        ],
        ROOT,
    )


def build_frontend() -> None:
    run([resolve_command("tsc"), "-b"], FRONTEND)
    run([resolve_command("vite"), "build"], FRONTEND)


def package_desktop() -> None:
    clean_package_output()
    run([resolve_command("electron-builder"), "--win", "portable"], FRONTEND)


def main() -> None:
    if sys.platform != "win32":
        raise SystemExit("desktop packaging currently targets Windows portable builds")
    clean_package_output()
    build_backend()
    build_frontend()
    package_desktop()


if __name__ == "__main__":
    main()
