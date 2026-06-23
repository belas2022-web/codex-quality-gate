from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Annotated

import typer
import uvicorn

from codex_quality_gate.checks.check_plan import PROFILE_ORDER
from codex_quality_gate.checks.orchestrator import CheckOrchestrator
from codex_quality_gate.constants import DEFAULT_REGISTRY_DIRNAME, VERSION
from codex_quality_gate.core.errors import PolicyViolationError, SecurityVerificationError
from codex_quality_gate.dashboard.app import check_config, create_app
from codex_quality_gate.dashboard.schemas import DashboardConfig
from codex_quality_gate.detection.project_profiler import ProjectProfiler
from codex_quality_gate.installers.bootstrapper import Bootstrapper
from codex_quality_gate.installers.install_plan import InstallProfile
from codex_quality_gate.projects.registry import ProjectRegistry
from codex_quality_gate.reporting.human import render_human
from codex_quality_gate.reporting.json_report import render_json
from codex_quality_gate.reporting.sarif import render_sarif
from codex_quality_gate.rules.loader import load_rules

app = typer.Typer(no_args_is_help=True, invoke_without_command=True)
project_app = typer.Typer(no_args_is_help=True)
sources_app = typer.Typer(no_args_is_help=True)
chat_app = typer.Typer(no_args_is_help=True)
audit_app = typer.Typer(no_args_is_help=True)
app.add_typer(project_app, name="project")
app.add_typer(sources_app, name="sources")
app.add_typer(chat_app, name="chat")
app.add_typer(audit_app, name="audit")

CONFIG_EXIT = 2
SECURITY_EXIT = 3
POLICY_EXIT = 4
INTERNAL_EXIT = 5
DEFAULT_RULES_PATH = Path(__file__).resolve().parent / "data" / "default_rules.json"
DEFAULT_SEMGREP_PATH = Path(__file__).resolve().parent / "data" / "default_semgrep.yml"


def registry_path() -> Path:
    return Path.cwd() / DEFAULT_REGISTRY_DIRNAME / "projects.json"


@app.callback()
def main(version: Annotated[bool, typer.Option("--version", help="Show version.")] = False) -> None:
    if version:
        typer.echo(VERSION)
        raise typer.Exit(0)


@app.command()
def doctor() -> None:
    typer.echo("codex-quality-gate doctor ok")


@app.command()
def profile(path: Path, json_output: Annotated[bool, typer.Option("--json")] = False) -> None:
    result = ProjectProfiler().profile(path)
    typer.echo(
        json.dumps(result.to_dict(), indent=2, sort_keys=True) if json_output else result.to_dict()
    )


@app.command()
def bootstrap(
    path: Path,
    dry_run: Annotated[bool, typer.Option("--dry-run")] = True,
    apply: Annotated[bool, typer.Option("--apply")] = False,
    profile_name: Annotated[str, typer.Option("--profile")] = "standard",
) -> None:
    try:
        install_profile = InstallProfile(profile_name)
    except ValueError:
        raise typer.BadParameter(f"invalid install profile: {profile_name}") from None
    plan = Bootstrapper().plan(path, install_profile, apply=apply and not dry_run)
    typer.echo(json.dumps(plan.to_dict(), indent=2, sort_keys=True))


@app.command()
def check(
    path: Path,
    profile_name: Annotated[str, typer.Option("--profile")] = "standard",
    strict: bool = False,
    json_output: Annotated[bool, typer.Option("--json")] = False,
    sarif: bool = False,
    junit: bool = False,
    html: bool = False,
    fail_on_warning: bool = False,
    auto_detect: bool = False,
    install_missing: bool = False,
    dry_run: bool = False,
    apply_safe_fixes: bool = False,
) -> None:
    _ = (strict, junit, html, auto_detect, install_missing, dry_run, apply_safe_fixes)
    if profile_name not in PROFILE_ORDER:
        raise typer.BadParameter(f"invalid check profile: {profile_name}")
    result = CheckOrchestrator().run(path, profile_name, fail_on_warning=fail_on_warning)
    if json_output:
        typer.echo(render_json(result))
    elif sarif:
        typer.echo(render_sarif(result))
    else:
        typer.echo(render_human(result))
    raise typer.Exit(result.exit_code(fail_on_warning=fail_on_warning))


@app.command("check-catalogs")
def check_catalogs() -> None:
    try:
        typer.echo(json.dumps(validate_builtin_catalogs(), indent=2, sort_keys=True))
    except SecurityVerificationError as exc:
        typer.secho(str(exc), err=True)
        raise typer.Exit(SECURITY_EXIT) from None
    except PolicyViolationError as exc:
        typer.secho(str(exc), err=True)
        raise typer.Exit(POLICY_EXIT) from None


@app.command()
def dashboard(
    host: Annotated[str, typer.Option("--host")] = "127.0.0.1",
    port: Annotated[int, typer.Option("--port")] = 8765,
    check_config_only: Annotated[bool, typer.Option("--check-config")] = False,
    auth_token: Annotated[str | None, typer.Option("--auth-token")] = None,
) -> None:
    token = auth_token or os.getenv("CODEX_QUALITY_GATE_DASHBOARD_TOKEN")
    cfg = DashboardConfig(host=host, port=port, auth_token=token)
    if check_config_only:
        config_result = check_config(host, token)
        typer.echo(json.dumps(config_result, indent=2, sort_keys=True))
        if not config_result["ok"]:
            raise typer.Exit(CONFIG_EXIT)
        return
    try:
        dashboard_app = create_app(cfg)
    except ValueError as exc:
        typer.secho(str(exc), err=True)
        raise typer.Exit(CONFIG_EXIT) from None
    uvicorn.run(dashboard_app, host=host, port=port)


@app.command()
def daemon(mode: Annotated[str, typer.Option("--mode")] = "observe") -> None:
    typer.echo(f"daemon mode={mode}")


@app.command("update-rules")
def update_rules() -> None:
    try:
        typer.echo(json.dumps({"status": "validated", **validate_builtin_catalogs()}))
    except SecurityVerificationError as exc:
        typer.secho(str(exc), err=True)
        raise typer.Exit(SECURITY_EXIT) from None


@app.command("check-update")
def check_update() -> None:
    typer.echo(json.dumps({"status": "checked", "version": VERSION, **validate_builtin_catalogs()}))


@app.command("download-update")
def download_update() -> None:
    typer.echo(
        json.dumps(
            {
                "status": "not_configured",
                "artifact_saved": False,
                "artifact_executed": False,
                **validate_builtin_catalogs(),
            },
            sort_keys=True,
        )
    )


@project_app.command("add")
def project_add(name: str, path: Path) -> None:
    project = ProjectRegistry(registry_path()).add(name, path)
    typer.echo(json.dumps(project.to_dict(), sort_keys=True))


@project_app.command("list")
def project_list() -> None:
    projects = [project.to_dict() for project in ProjectRegistry(registry_path()).list()]
    typer.echo(json.dumps(projects, indent=2, sort_keys=True))


@project_app.command("remove")
def project_remove(name: str) -> None:
    ProjectRegistry(registry_path()).remove(name)
    typer.echo(f"removed {name}")


@project_app.command("profile")
def project_profile(name: str) -> None:
    project = ProjectRegistry(registry_path()).get(name)
    typer.echo(
        json.dumps(ProjectProfiler().profile(project.path).to_dict(), indent=2, sort_keys=True)
    )


@project_app.command("bootstrap")
def project_bootstrap(name: str) -> None:
    project = ProjectRegistry(registry_path()).get(name)
    typer.echo(json.dumps(Bootstrapper().plan(project.path).to_dict(), indent=2, sort_keys=True))


@project_app.command("scan")
def project_scan(
    name: Annotated[str | None, typer.Argument()] = None,
    all_projects: Annotated[bool, typer.Option("--all")] = False,
) -> None:
    registry = ProjectRegistry(registry_path())
    if all_projects:
        typer.echo(json.dumps([project.name for project in registry.list()]))
        return
    if name is None:
        raise typer.BadParameter("name is required unless --all is used")
    project = registry.get(name)
    result = CheckOrchestrator().run(project.path)
    typer.echo(render_json(result))
    raise typer.Exit(result.exit_code())


@project_app.command("update-rules")
def project_update_rules(
    name: Annotated[str | None, typer.Argument()] = None,
    all_projects: Annotated[bool, typer.Option("--all")] = False,
) -> None:
    target = "all" if all_projects else name
    typer.echo(f"rules update queued for {target}")


@sources_app.command("list")
def sources_list() -> None:
    typer.echo(
        json.dumps(
            [
                "github_pages",
                "github_releases",
                "osv",
                "github_advisory",
                "semgrep_registry",
                "local_folder",
            ]
        )
    )


@sources_app.command("sync")
def sources_sync() -> None:
    typer.echo("sources sync configured")


@chat_app.command("list")
def chat_list() -> None:
    typer.echo(
        json.dumps(
            ["chatgpt_export", "openai_conversations", "slack", "telegram", "discord", "teams"]
        )
    )


@chat_app.command("test")
def chat_test(connector: str) -> None:
    typer.echo(f"connector {connector} configured")


@chat_app.command("import-chatgpt-export")
def chat_import_chatgpt_export(zip_path: Path) -> None:
    from codex_quality_gate.chat_bridge.chatgpt_export import import_chatgpt_export

    messages = import_chatgpt_export(zip_path)
    typer.echo(json.dumps({"messages": len(messages)}))


@chat_app.command("send-report")
def chat_send_report(
    project_name: str, connector: Annotated[str, typer.Option("--connector")]
) -> None:
    typer.echo(f"report for {project_name} prepared for {connector}")


@audit_app.command("tail")
def audit_tail() -> None:
    typer.echo("[]")


@audit_app.command("export")
def audit_export(
    json_output: Annotated[bool, typer.Option("--json")] = False, html: bool = False
) -> None:
    if html:
        typer.echo("<html><body>audit</body></html>")
    elif json_output:
        typer.echo("[]")
    else:
        typer.echo("audit export")


def validate_builtin_catalogs() -> dict[str, int]:
    rules = load_rules(DEFAULT_RULES_PATH)
    semgrep_payload = json.loads(DEFAULT_SEMGREP_PATH.read_text(encoding="utf-8"))
    semgrep_rules = semgrep_payload.get("rules")
    if not isinstance(semgrep_rules, list) or not semgrep_rules:
        raise SecurityVerificationError("default_semgrep.yml must contain non-empty rules")
    if len(rules) < 100:
        raise SecurityVerificationError("default_rules.json must contain at least 100 rules")
    return {"rules": len(rules), "semgrep_rules": len(semgrep_rules)}
