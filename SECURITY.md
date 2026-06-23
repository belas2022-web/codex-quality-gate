# Security Policy

## Update Threat Model

Rule and app updates are untrusted until they pass every gate: HTTPS URL,
allowlisted domain, SHA-256 digest, Ed25519 signature, version checks, backup,
rollback plan, and exclusive update lock. Hashes do not replace signatures.

## Chat Threat Model

Chat connectors only use official APIs, OAuth/token flows, webhooks, or user
exports. UI scraping is not implemented. Reading requires allowlisted sources.
Write-back requires explicit write permission. Full source code is blocked by
default and secrets are redacted before storage or sending.

## Secret Handling

Secrets are read only from environment variables or local config. They must not be
committed, logged, sent in chat reports, or stored in audit payloads.

## Allowed Domains

The default allowlist covers `belas.github.io`, GitHub release hosts, and local
offline folders. Add domains intentionally and review them like security code.

## Ed25519 And SHA-256

Manifests, rules files, Semgrep rules, and app artifacts must have SHA-256 and
Ed25519 verification. On mismatch, reject the update and keep the previous version.

## Rollback

Rule replacement is atomic and backed up first. Failed writes restore the backup.

## Audit Logging

Dangerous actions, update checks, policy violations, chat events, and scan runs are
written to audit logs with redaction.

## No Auto-Execute

Downloaded artifacts are verified and cached. They are never executed automatically.

## Windows UTF-8 Mode

The check runner sets `PYTHONUTF8=1` and `PYTHONIOENCODING=utf-8` for subprocesses.
When running third-party security tools directly on Windows, especially from paths
with non-ASCII characters, set the same environment variables before invoking the
tool if it raises an encoding error.

## No Root/Admin Install

Installers do not use sudo/admin. Bootstrap is dry-run by default and real install
actions require `--apply`.

## Key Rotation

Publish a new signed manifest containing the new public key metadata, overlap old
and new keys for one release, and keep old manifests archived for audit.

## Reporting Vulnerabilities

Open a private security advisory or send a minimal report without secrets. Include
affected version, reproduction steps, impact, and suggested mitigation.
