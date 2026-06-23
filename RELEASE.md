# Release Checklist

## v0.1.0 Stable Criteria

Use the hosted release workflow for the stable release. A local build is useful
for mechanics, but it does not validate hosted CI
permissions, tag workflows, uploaded artifacts, or GitHub Release publishing.

1. Commit the release-prep changes.
2. Replace the development Ed25519 public key in code and generated defaults.
3. Add a matching GitHub Actions secret named `RELEASE_ED25519_PRIVATE_KEY_B64`.
4. Push to the real remote.
5. Clone the real remote into an ASCII-only path.
6. Install Python and frontend dependencies.
7. Run the full release gate from the clean clone.
8. Confirm hosted CI is green.
9. Tag `v0.1.0`.
10. Confirm the release workflow uploads wheel, sdist, rules, Semgrep bundle,
   `SHA256SUMS`, and `latest.json`.
11. Confirm GitHub Release assets match the workflow artifacts.

`v0.1.0-rc1` was published and CI-verified, but it is superseded by `v0.1.0-rc2`
because field validation found a Semgrep resolver failure on external projects.
`v0.1.0-rc3` keeps the `v0.1.0-rc2` fixes and adds autonomous release
publishing. Stable `v0.1.0` keeps those fixes and requires signed metadata.

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

The release update channel must publish metadata and artifacts:

- `codex_quality_gate-0.1.0-py3-none-any.whl`
- `codex_quality_gate-0.1.0.tar.gz`
- rules JSON bundle
- Semgrep bundle
- SHA-256 hashes
- Ed25519 signatures
- `latest.json`
- manifest signature

Release candidates may be published as `unsigned-rc` while the release workflow
is being rehearsed. Stable releases must set `RELEASE_ED25519_PRIVATE_KEY_B64`;
the workflow blocks stable metadata generation when the signing key is absent,
when the packaged public key is still the development placeholder, or when the
private key does not match the packaged public key.

When signatures are present, verify that manifest signatures, rules signatures,
rules hashes, artifact signatures, and artifact hashes all match. Downloaded
artifacts must be verified and cached, never executed automatically.

## Stable Release Criteria

Do not cut `v0.1.0` stable until:

- Real remote CI is green.
- `v0.1.0-rc3` installs from artifact.
- Update manifest and signatures are verified.
- The gate has been tested on 2-3 real projects.
- There are no P1 or P2 findings.
- Known warnings are documented in README, SECURITY, and CHANGELOG.
