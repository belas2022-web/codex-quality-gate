# Release Checklist

## v0.1.0-rc1 Criteria

Use a real remote repository for the final release-candidate rehearsal. A local
bare origin is useful for git mechanics, but it does not validate hosted CI,
permissions, tag workflows, or release artifacts.

1. Commit the release-prep changes.
2. Push to the real remote.
3. Clone the real remote into an ASCII-only path.
4. Install Python and frontend dependencies.
5. Run the full release gate from the clean clone.
6. Confirm hosted CI is green.
7. Tag `v0.1.0-rc1`.
8. Build and sign RC artifacts.

## Clean Clone Gate

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

Expected result:

- All checks pass.
- Coverage stays at or above the project threshold.
- Security and full profiles exit 0.
- Frontend lint, typecheck, build, and audit pass.
- `git_diff_policy` is not skipped in a real git repo.

## Git Policy Probe

On a temporary branch, confirm the policy reacts to risky diffs:

- Deleting tests is blocked.
- `.env` and secret-bearing files are blocked.
- CI, security, auth, chat bridge, updater, and dashboard changes require review
  or fail according to policy.

## Signed Artifacts

The release update channel must publish signed metadata and artifacts:

- `codex_quality_gate-0.1.0rc1-py3-none-any.whl`
- `codex_quality_gate-0.1.0rc1.tar.gz`
- rules JSON bundle
- Semgrep bundle
- SHA-256 hashes
- Ed25519 signatures
- `latest.json`
- manifest signature

Verify that manifest signatures, rules signatures, rules hashes, artifact
signatures, and artifact hashes all match. Downloaded artifacts must be verified
and cached, never executed automatically.

## Stable Release Criteria

Do not cut `v0.1.0` stable until:

- Real remote CI is green.
- `v0.1.0-rc1` installs from artifact.
- Update manifest and signatures are verified.
- The gate has been tested on 2-3 real projects.
- There are no P1 or P2 findings.
- Known warnings are documented in README, SECURITY, and CHANGELOG.
