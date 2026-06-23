from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Bootstrap codex-quality-gate.")
    parser.add_argument("--dry-run", action="store_true", default=True)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument(
        "--profile", choices=["minimal", "standard", "security", "full"], default="standard"
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if sys.version_info < (3, 11):  # noqa: UP036 - bootstrap must validate Python explicitly.
        print("Python 3.11 or newer is required.", file=sys.stderr)
        return 2
    commands = [
        [sys.executable, "-m", "venv", ".venv"],
        [
            str(Path(".venv") / ("Scripts" if sys.platform == "win32" else "bin") / "python"),
            "-m",
            "pip",
            "install",
            "-e",
            ".[dev]",
        ],
        [sys.executable, "-m", "codex_quality_gate", "doctor"],
        [sys.executable, "-m", "pytest", "-q"],
    ]
    if not args.apply:
        print(f"dry-run profile={args.profile}")
        for command in commands:
            print(" ".join(command))
        return 0
    for command in commands:
        completed = subprocess.run(command, check=False, timeout=600)
        if completed.returncode != 0:
            return completed.returncode
    print("Next: python -m codex_quality_gate check .")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
