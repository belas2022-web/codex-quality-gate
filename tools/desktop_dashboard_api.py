from __future__ import annotations

import argparse

from codex_quality_gate.cli import run_dashboard_api


def main() -> None:
    parser = argparse.ArgumentParser(description="codex-quality-gate desktop dashboard API")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--auth-token", default=None)
    args = parser.parse_args()
    run_dashboard_api(
        host=args.host,
        port=args.port,
        check_config_only=False,
        auth_token=args.auth_token,
    )


if __name__ == "__main__":
    main()
