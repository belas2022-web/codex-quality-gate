from __future__ import annotations

import importlib
import json
import pkgutil
from pathlib import Path
from typing import Any

import codex_quality_gate
from codex_quality_gate.chat_bridge.base import HttpTransport
from codex_quality_gate.chat_bridge.discord import DiscordConnector
from codex_quality_gate.chat_bridge.memory import summarize_messages
from codex_quality_gate.chat_bridge.openai_conversations import OpenAIConversationsConnector
from codex_quality_gate.chat_bridge.permissions import ChatPermissions
from codex_quality_gate.chat_bridge.slack import SlackConnector
from codex_quality_gate.chat_bridge.teams import TeamsConnector
from codex_quality_gate.chat_bridge.telegram import TelegramConnector
from codex_quality_gate.checks.registry import available_checks
from codex_quality_gate.core.environment import get_env_name, require_env_name
from codex_quality_gate.core.logging import configure_logging
from codex_quality_gate.core.result import ProjectProfile, ScanResult
from codex_quality_gate.database.migrations import apply_migrations
from codex_quality_gate.database.models import StoredFinding
from codex_quality_gate.database.sqlite import connect
from codex_quality_gate.detection.ci_detector import detect_ci
from codex_quality_gate.installers.bootstrapper import Bootstrapper
from codex_quality_gate.installers.install_plan import InstallPlan, InstallProfile, ToolRequirement
from codex_quality_gate.projects.registry import ProjectRegistry
from codex_quality_gate.projects.workspace import workspace_state_dir
from codex_quality_gate.reporting.human import render_human
from codex_quality_gate.rules.loader import load_rules
from codex_quality_gate.rules.rule_engine import default_rules
from codex_quality_gate.rules.semgrep_exporter import export_semgrep_rules
from codex_quality_gate.scanner.ast_scanner import parse_python
from codex_quality_gate.scanner.ignore import is_ignored
from codex_quality_gate.scanner.regex_scanner import find_regex
from codex_quality_gate.update_sources.azure_blob import AzureBlobSource
from codex_quality_gate.update_sources.base import UpdateSource
from codex_quality_gate.update_sources.cloudflare_r2 import CloudflareR2Source
from codex_quality_gate.update_sources.docker_registry import DockerRegistrySource
from codex_quality_gate.update_sources.github_advisory import GitHubAdvisorySource
from codex_quality_gate.update_sources.github_pages import GitHubPagesSource
from codex_quality_gate.update_sources.gitlab_releases import GitLabReleasesSource
from codex_quality_gate.update_sources.google_cloud_storage import GoogleCloudStorageSource
from codex_quality_gate.update_sources.local_folder import LocalFolderSource
from codex_quality_gate.update_sources.npm import NpmSource
from codex_quality_gate.update_sources.nvd import NvdSource
from codex_quality_gate.update_sources.openai_codex import OpenAICodexSource
from codex_quality_gate.update_sources.osv import OsvSource
from codex_quality_gate.update_sources.pypi import PyPISource
from codex_quality_gate.update_sources.s3 import S3Source
from codex_quality_gate.update_sources.semgrep_registry import SemgrepRegistrySource
from codex_quality_gate.updates.cache import cache_payload
from codex_quality_gate.updates.hashing import sha256_file
from codex_quality_gate.updates.models import UpdateManifest
from codex_quality_gate.updates.rollback import rollback_file
from codex_quality_gate.updates.update_client import UpdateClient
from codex_quality_gate.updates.updater import Updater
from codex_quality_gate.workers.daemon import Daemon
from codex_quality_gate.workers.jobs import ScanJob
from codex_quality_gate.workers.queue import Job, JobQueue


class FakeResponse:
    def __init__(self, payload: Any, content: bytes = b"payload", url: str = "") -> None:
        self.payload = payload
        self.content = content
        self.url = url or str(payload.get("url", "")) if isinstance(payload, dict) else url
        self.status_code = 200
        self.headers = {"Content-Length": str(len(content))}

    def json(self) -> Any:
        return self.payload

    def raise_for_status(self) -> None:
        return None

    def iter_content(self, chunk_size: int = 65536):
        _ = chunk_size
        yield self.content


class FakeTransport(HttpTransport):
    def __init__(self, payload: Any) -> None:
        self.payload = payload

    def get(self, _url: str, **_kwargs: Any) -> FakeResponse:
        return FakeResponse(self.payload)

    def post(self, url: str, **kwargs: Any) -> FakeResponse:
        return FakeResponse({"ok": True, "url": url, "kwargs": kwargs})


class FakeSession:
    def get(self, url: str, **kwargs: Any) -> FakeResponse:
        timeout = kwargs["timeout"]
        payload = {"url": url, "timeout": timeout}
        if url.endswith("latest.json"):
            return FakeResponse(
                payload,
                content=b'{"url": "https://good.example/latest.json", "timeout": 3.0}',
                url=url,
            )
        return FakeResponse(payload, content=b"bytes", url=url)


class FakeClient:
    def __init__(self, payload: bytes) -> None:
        self.payload = payload

    def get_bytes(self, _url: str) -> bytes:
        return self.payload

    def get_json(self, url: str) -> dict[str, Any]:
        return {"url": url}


def test_imports_all_package_modules() -> None:
    package_path = Path(codex_quality_gate.__file__).parent
    module_names = [
        item.name
        for item in pkgutil.walk_packages([str(package_path)], prefix="codex_quality_gate.")
    ]
    for module_name in module_names:
        importlib.import_module(module_name)


def test_smoke_helpers_and_sources(tmp_path: Path, monkeypatch: Any) -> None:
    assert available_checks()
    assert get_env_name("MISSING_CODEX_QUALITY_GATE_ENV") is None
    monkeypatch.setenv("CODEX_QUALITY_GATE_SAMPLE", "value")
    assert require_env_name("CODEX_QUALITY_GATE_SAMPLE") == "value"
    configure_logging()
    assert detect_ci(tmp_path) == []
    assert workspace_state_dir(tmp_path).name == ".codex-quality-gate"
    assert not is_ignored(tmp_path / "x.py", tmp_path)
    assert find_regex("abc", "x\nabc")[0].line == 2
    assert parse_python("x = 1") is not None
    assert parse_python("x =") is None
    empty_result = ScanResult("demo", ProjectProfile(tmp_path), [])
    assert render_human(empty_result) == "No findings."
    assert "pattern-regex" in export_semgrep_rules(default_rules()[:1])

    rules_path = tmp_path / "rules.json"
    rules_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "rules_version": "test",
                "minimum_app_version": "0.1.0",
                "rules": [
                    {
                        "id": "x",
                        "title": "x",
                        "regex": "abc",
                        "message": "abc found",
                        "severity": "warning",
                        "category": "demo",
                        "languages": ["python"],
                        "extensions": [".py"],
                        "repair_hint": "replace abc",
                        "fix_strategy": "manual",
                        "tags": ["demo"],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    assert load_rules(rules_path)[0].id == "x"

    connection = connect(tmp_path / "db.sqlite")
    apply_migrations(connection)
    stored = StoredFinding(1, "r", "x.py", "warning", "message")
    assert stored.rule_id == "r"

    cached = cache_payload(tmp_path / "cache", "x.bin", b"x")
    assert cached.read_bytes() == b"x"
    source = tmp_path / "source.txt"
    backup = tmp_path / "backup.txt"
    source.write_text("old", encoding="utf-8")
    backup.write_text("new", encoding="utf-8")
    rollback_file(source, backup, base_dir=tmp_path)
    assert source.read_text(encoding="utf-8") == "new"
    assert sha256_file(source)

    update_source = UpdateSource("local", "local", True, 1, {})
    assert update_source.name == "local"
    for source_cls in [
        AzureBlobSource,
        CloudflareR2Source,
        DockerRegistrySource,
        GitHubAdvisorySource,
        GitLabReleasesSource,
        GoogleCloudStorageSource,
        LocalFolderSource,
        NpmSource,
        NvdSource,
        OpenAICodexSource,
        OsvSource,
        PyPISource,
        S3Source,
        SemgrepRegistrySource,
    ]:
        assert source_cls(enabled=True).latest()["enabled"]


def test_http_update_clients_and_updater_paths() -> None:
    update_client = UpdateClient(FakeSession(), timeout=3.0)  # type: ignore[arg-type]
    assert update_client.get_json("https://good.example/latest.json")["timeout"] == 3.0
    assert update_client.get_bytes("https://good.example/file") == b"bytes"

    pages = GitHubPagesSource(
        "https://good.example/latest.json",
        client=FakeClient(b"rules"),  # type: ignore[arg-type]
    )
    assert pages.latest()["url"].endswith("latest.json")

    manifest = UpdateManifest.from_dict(
        {
            "version": "1.0.0",
            "created_at": "now",
            "expires_at": "later",
            "rules_url": "https://good.example/rules",
            "rules_sha256": "bad",
            "rules_signature": "bad",
            "app_artifact_url": "https://good.example/app",
            "app_artifact_sha256": "bad",
            "app_artifact_signature": "bad",
        }
    )
    updater = Updater(["good.example"], "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=")
    assert updater.allowed_domains == ["good.example"]
    assert manifest.canonical_bytes()


def test_chat_connectors_with_mock_transport() -> None:
    permissions = ChatPermissions(
        allowed_read_ids={"C1", "123", "D1", "T1", "O1"},
        allowed_write_ids={"C1", "123", "D1", "T1", "O1"},
        writeback_allowed=True,
    )
    slack = SlackConnector(
        "token",
        permissions,
        FakeTransport({"messages": [{"user": "u", "text": "hello"}]}),  # type: ignore[arg-type]
    )
    assert slack.list_messages("C1")[0].text == "hello"
    assert slack.send_report("C1", "report")["ok"]

    telegram = TelegramConnector(
        "token",
        permissions,
        FakeTransport({"result": [{"message": {"chat": {"id": 123}, "text": "hello"}}]}),  # type: ignore[arg-type]
    )
    assert telegram.list_messages("123")[0].text == "hello"
    assert telegram.send_report("123", "report")["ok"]

    discord = DiscordConnector(
        "token",
        permissions,
        FakeTransport([{"author": {"id": "u"}, "content": "hello"}]),  # type: ignore[arg-type]
    )
    assert discord.list_messages("D1")[0].text == "hello"
    assert discord.send_report("D1", "report")["ok"]

    teams = TeamsConnector(
        "token",
        permissions,
        FakeTransport({"value": [{"from": {"user": "u"}, "body": {"content": "hello"}}]}),  # type: ignore[arg-type]
    )
    assert teams.list_messages("T1")[0].text == "hello"
    assert teams.send_report("T1", "report")["ok"]

    openai = OpenAIConversationsConnector(
        "token",
        permissions,
        FakeTransport({"data": [{"role": "user", "content": "hello"}]}),  # type: ignore[arg-type]
    )
    assert openai.list_messages("O1")[0].text == "hello"
    assert openai.send_report("O1", "report")["ok"]
    assert summarize_messages(openai.list_messages("O1")) == {"messages": 1}


def test_workers_and_bootstrapper_smoke(tmp_path: Path) -> None:
    queue = JobQueue()
    assert queue.pop() is None
    queue.push(Job("scan", {"project": "demo"}))
    assert queue.pop().name == "scan"
    scan_job = ScanJob("demo")
    assert scan_job.project_name == "demo"

    registry = ProjectRegistry(tmp_path / "projects.json")
    registry.add("demo", tmp_path)
    assert Daemon(registry).run_once() == {"demo": True}

    plan = InstallPlan(
        InstallProfile.MINIMAL,
        dry_run=True,
        requirements=[ToolRequirement("noop", "noop", ("python", "--version"))],
    )
    assert Bootstrapper().execute(plan) == ["dry-run: python --version"]
