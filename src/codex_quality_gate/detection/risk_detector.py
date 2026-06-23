from __future__ import annotations

from pathlib import Path

from codex_quality_gate.core.result import RiskProfile
from codex_quality_gate.scanner.ignore import iter_project_files

RISK_KEYWORDS: dict[str, tuple[str, ...]] = {
    "has_updater": ("updater", "update", "manifest", "signature"),
    "has_network": ("requests.", "httpx.", "fetch(", "axios", "urllib"),
    "has_auth": ("auth", "oauth", "jwt", "token"),
    "has_database": ("sqlite", "sqlalchemy", "migrations", "database"),
    "has_chat_bridge": ("slack", "telegram", "discord", "teams", "chat_bridge"),
    "has_dashboard": ("fastapi", "dashboard", "vite", "react"),
    "has_secret_handling": ("secret", "api_key", "password", "token"),
    "has_file_writes": ("write_text(", "open(", "replace("),
    "has_archive_extraction": ("zipfile", "tarfile", "extract"),
    "has_subprocess": ("subprocess.", "Popen("),
    "has_public_api": ("fastapi", "flask", "express", "router"),
}


def detect_risk(root: Path) -> RiskProfile:
    text = ""
    suffixes = {".py", ".js", ".ts", ".tsx", ".json", ".yml", ".yaml"}
    for path in iter_project_files(root, suffixes):
        try:
            text += "\n" + path.read_text(encoding="utf-8", errors="ignore").lower()
        except OSError:
            continue
    flags: dict[str, bool] = {}
    for field, markers in RISK_KEYWORDS.items():
        flags[field] = any(marker.lower() in text for marker in markers)
    flags["has_docker"] = any(
        (root / name).exists() for name in ("Dockerfile", "docker-compose.yml", "compose.yml")
    )
    flags["has_ci"] = (root / ".github" / "workflows").exists() or (
        root / ".gitlab-ci.yml"
    ).exists()
    return RiskProfile(**flags)
