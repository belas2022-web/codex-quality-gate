# Contributing

Run the full local gate before sending changes:

```bash
python -m ruff check .
python -m ruff format --check .
python -m mypy .
python -m pytest -q
python -m pytest --cov
python -m codex_quality_gate check . --fail-on-warning
```

Security, updater, auth, chat_bridge, migrations, and CI changes require review.
