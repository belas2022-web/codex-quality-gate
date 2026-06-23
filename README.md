# codex-quality-gate

`codex-quality-gate` is an autonomous multi-project quality gate for code written
with AI and Codex. It profiles repositories, builds a check plan, runs safe local
checks, stores findings, exposes a local dashboard, protects risky areas with
policies, and supports signed rule/update metadata.

The generated defaults replace the original placeholders:

- App name: `codex-quality-gate`
- GitHub owner: `belas`
- Rules updates repository: `codex-quality-gate-updates`
- App releases repository: `codex-quality-gate-releases`
- Ed25519 public key: development placeholder only, replace before stable release
- Token environment names: `SLACK_APP_TOKEN`, `TELEGRAM_BOT_TOKEN`,
  `DISCORD_BOT_TOKEN`, `TEAMS_CLIENT_ID`, `OPENAI_API_KEY`

## Quick Start

```bash
python -m venv .venv
.venv\Scripts\python -m pip install -e ".[dev]"
.venv\Scripts\python -m codex_quality_gate doctor
.venv\Scripts\python -m codex_quality_gate profile . --json
.venv\Scripts\python -m codex_quality_gate check .
```

Linux/macOS shells use `.venv/bin/python` instead of `.venv\Scripts\python`.

## Release Rehearsal

Before tagging a release candidate, run the full gate from a clean clone in an
ASCII-only path. Install frontend dependencies before running the root full
profile, because the full profile invokes frontend checks when a frontend is
present.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip setuptools wheel
python -m pip install -e ".[dev]"

$env:npm_config_cache="$PWD\.npm-cache"
cd frontend
npm ci
npm run lint
npm run typecheck
npm run test
npm run build
npm audit --json
cd ..

python -m ruff check .
python -m ruff format --check .
python -m mypy .
python -m pytest -q
python -m pytest --cov
python -m codex_quality_gate check-catalogs
python -m codex_quality_gate check . --json
python -m codex_quality_gate check . --sarif
python -m codex_quality_gate check . --fail-on-warning
python -m codex_quality_gate check . --profile security --json
python -m codex_quality_gate check . --profile full --json
python -m bandit -q -r src -ll
python -m pip_audit
.\.venv\Scripts\semgrep --config src\codex_quality_gate\data\default_semgrep.yml src
python -m build
pip check
```

The project-local npm cache is optional, but useful on Windows machines where a
global npm cache has permissions problems. `.npm-cache/` is ignored.

See `RELEASE.md` for the remote-clone release checklist and signed artifact
requirements.

## Installers

`bootstrap.py` is dry-run by default:

```bash
python bootstrap.py --dry-run
python bootstrap.py --profile security
python bootstrap.py --apply --profile standard
```

`install.sh` and `install.ps1` run `python bootstrap.py --apply`. They do not use
sudo/admin and do not install global packages.

## Add And Scan Projects

```bash
codex-quality-gate project add backend-api /path/to/backend-api
codex-quality-gate project list
codex-quality-gate project scan backend-api
codex-quality-gate project scan --all
```

## CLI

```bash
codex-quality-gate --version
codex-quality-gate doctor
codex-quality-gate profile . --json
codex-quality-gate bootstrap . --dry-run
codex-quality-gate check . --json
codex-quality-gate check . --sarif
codex-quality-gate dashboard --host 127.0.0.1 --port 8765
codex-quality-gate daemon --mode observe
codex-quality-gate update-rules
codex-quality-gate sources list
codex-quality-gate chat list
codex-quality-gate audit tail
```

## Architecture

- `detection`: project stack, package manager, CI, framework, and risk profiling.
- `installers`: tool catalog, dry-run install plans, explicit `--apply` execution.
- `checks`: check plans and orchestration over profiled projects.
- `rules`: signed JSON rule schema and the built-in AI/Codex rule engine.
- `scanner`: filesystem, regex, AST, and diff scanning helpers.
- `updates`: HTTPS allowlist, SHA-256, Ed25519 signatures, backup, rollback, lock.
- `projects`: multi-project registry, per-project config, and scan locks.
- `database`: SQLite persistence for runs, findings, updates, audit, policies.
- `dashboard`: FastAPI dashboard API, localhost by default.
- `chat_bridge`: official API/export-only connectors with permissions.
- `policies`: blocks dangerous autofix and Codex changes.
- `audit`: JSONL audit events with secret redaction.

## Security Model

Updates must be HTTPS, domain-allowlisted, SHA-256 checked, and Ed25519 signed.
Downloaded app artifacts are verified and cached, never executed automatically.
Stable release metadata requires a real Ed25519 public key in the package and a
matching `RELEASE_ED25519_PRIVATE_KEY_B64` secret in GitHub Actions.
Chat connectors never scrape UIs and require explicit read/write allowlists.
Secrets are redacted from audit records and outgoing chat reports.

## Connecting Update Sources

GitHub Pages reads `https://belas.github.io/codex-quality-gate-updates/latest.json`.
GitHub Releases reads `belas/codex-quality-gate-releases`. OSV and Semgrep sources
are represented as safe source descriptors; tests mock all network calls.

## Connecting Chats

Slack, Telegram, Discord, Teams, and OpenAI connectors are disabled by default.
Enable a connector in config, set the named environment variable locally, and add
allowed read/write channel or chat IDs. Write-back requires permission.

## Examples

JSON output:

```bash
codex-quality-gate check . --json
```

SARIF output:

```bash
codex-quality-gate check . --sarif > reports.sarif
```

## Troubleshooting

- If `python -m codex_quality_gate` is not found, install editable with `pip install -e .`.
- If dashboard is bound outside localhost, configure auth first.
- If an update is rejected, check domain allowlist, SHA-256, signature, and version.
- If a chat report is blocked, check connector permissions and write-back settings.
- On Windows paths with non-ASCII characters, set `PYTHONUTF8=1` if a third-party
  tool such as `pip-audit` raises `UnicodeDecodeError`.

## Known Limitations

The project ships production-safe connector skeletons and local scanning logic.
External services are only contacted when a connector/source is enabled and called.
The default signing key is a development placeholder and must be replaced before
stable release.
