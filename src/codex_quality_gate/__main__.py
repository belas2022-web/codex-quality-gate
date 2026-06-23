from __future__ import annotations

import click
from typer._click import exceptions as typer_click_exceptions
from typer.main import get_command

from codex_quality_gate.cli import app

if __name__ == "__main__":
    command = get_command(app)
    try:
        exit_code = command.main(prog_name="python -m codex_quality_gate", standalone_mode=False)
        if isinstance(exit_code, int):
            raise SystemExit(exit_code)
    except typer_click_exceptions.Exit as exc:
        raise SystemExit(exc.exit_code) from None
    except (typer_click_exceptions.UsageError, typer_click_exceptions.BadParameter) as exc:
        exc.show()
        raise SystemExit(2) from None
    except typer_click_exceptions.ClickException as exc:
        exc.show()
        raise SystemExit(1) from None
    except click.exceptions.Exit as exc:
        raise SystemExit(exc.exit_code) from None
    except click.UsageError as exc:
        exc.show()
        raise SystemExit(2) from None
    except click.ClickException as exc:
        exc.show()
        raise SystemExit(1) from None
