# Changelog

## 0.1.0rc3

Status: release candidate.

- Adds an autonomous tag-driven release workflow that reruns the full quality,
  security, frontend, and package gate before publishing release assets.
- Generates wheel, sdist, rules bundle, Semgrep bundle, `SHA256SUMS`, and
  `latest.json` release metadata from CI.
- Signs artifacts and the update manifest when `RELEASE_ED25519_PRIVATE_KEY_B64`
  is configured, and blocks stable releases without a signing key.
- Keeps release candidates publishable as unsigned RC artifacts so the pipeline
  can be rehearsed before stable signing is enabled.

## 0.1.0rc2

Status: release candidate.

- Supersedes `v0.1.0-rc1`, which was published but failed field validation on
  external projects.
- Fixed external project tool resolution so Semgrep is resolved from the target
  project virtualenv or the runner environment instead of falling back to
  `python -m semgrep` in target context.
- Added regression coverage for Windows Semgrep resolution from the runner
  environment.
- Confirmed invalid or non-repository `.git` directories are skipped by
  `git_diff_policy` instead of surfacing as `git diff` tool failures.
- Added regression coverage for broken `.git` directory handling.

## 0.1.0rc1

Status: superseded release candidate.

Known release-candidate issue:

- Failed field validation on external projects because Semgrep could be invoked
  as `python -m semgrep`, which exits with code 2 on newer Semgrep versions on
  Windows.

Passed:

- Clean clone release rehearsal in an ASCII path.
- Python quality suite.
- Security and full profiles.
- Semgrep, Bandit, and pip-audit.
- Frontend lint, typecheck, build, and audit.
- Dashboard auth enforcement.
- Audit write-time redaction.
- Git diff policy.
- Update redirect and path protections.
- Package build.

Known warnings:

- Frontend has no `npm test` script yet.
- Windows non-ASCII paths may require UTF-8 environment variables for direct
  third-party tool runs.
- Stable release requires validation on real remote CI and real projects.

## 0.1.0

- Initial release.
- Multi-project registry.
- Project profiler.
- Tool catalog.
- Bootstrapper.
- Check plan and orchestrator.
- Rule engine with built-in AI/Codex checks.
- Semgrep rule export.
- Secure rules update flow.
- Signed manifest and app artifact verification.
- Dashboard API and React dashboard.
- Daemon.
- ChatBridge connectors.
- Policy engine.
- Audit log.
- CLI.
- Tests and CI.
