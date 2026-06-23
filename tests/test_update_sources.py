from __future__ import annotations

from codex_quality_gate.update_sources.local_folder import LocalFolderSource


def test_local_folder_source_reports_enabled_state() -> None:
    assert LocalFolderSource(enabled=True).latest() == {
        "source": "local_folder",
        "enabled": True,
    }
    assert LocalFolderSource(enabled=False).latest()["enabled"] is False
