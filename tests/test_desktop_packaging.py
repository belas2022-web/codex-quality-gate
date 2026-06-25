from __future__ import annotations

import json
from pathlib import Path


def test_desktop_packaging_is_configured_without_browser_dashboard_scripts() -> None:
    package = json.loads(Path("frontend/package.json").read_text(encoding="utf-8"))

    assert package["scripts"]["desktop"] == "electron electron/main.cjs"
    assert package["scripts"]["desktop:package"] == "electron-builder --win portable"
    assert "dev" not in package["scripts"]
    assert "desktop:dev" not in package["scripts"]
    assert "electron-builder" in package["devDependencies"]

    build = package["build"]
    assert build["directories"]["output"] == "dist-desktop"
    assert build["extraResources"][0]["from"] == "desktop-backend"
    assert build["extraResources"][0]["to"] == "desktop-backend"
    assert build["win"]["signExecutable"] is False
    assert build["nsis"]["packElevateHelper"] is False


def test_desktop_build_script_uses_pyinstaller_and_no_shell_subprocesses() -> None:
    source = Path("tools/build_desktop.py").read_text(encoding="utf-8")

    assert "pyinstaller" in source
    assert "electron-builder" in source
    assert "desktop-backend" in source
    assert "clean_package_output" in source
    assert "shell=False" in source
    assert "shell=True" not in source
