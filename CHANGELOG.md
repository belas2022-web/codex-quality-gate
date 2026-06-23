# Changelog

## 0.1.0rc1

Status: release candidate.

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
