# AGENTS.md

## Definition of Done

Do not consider work complete until all checks pass:

```bash
python -m ruff check .
python -m ruff format --check .
python -m mypy .
python -m pytest -q
python -m pytest --cov
python -m codex_quality_gate check . --fail-on-warning
```

## Hard Rules

Do not delete tests.
Do not weaken assertions.
Do not disable CI.
Do not disable security checks.
Do not add dependencies without explanation.
Do not use dynamic code evaluation.
Do not launch subprocesses through a shell.
Do not use pickle for external data.
Do not disable TLS verification.
Do not auto-execute downloaded artifacts.
Keep patches minimal.
Add regression tests for every bug fix.
Report changed files and command results.
Changes to updater/security/auth/chat_bridge/CI require review.
