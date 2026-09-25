"""Machine preferences, separate from project scientific configuration."""

from __future__ import annotations

import json
from pathlib import Path


def settings_path() -> Path:
    path = Path.home() / ".pathview-plus"
    path.mkdir(parents=True, exist_ok=True)
    return path / "gui-settings.json"


def load_settings() -> dict:
    try:
        from PySide6.QtCore import QSettings

        settings = QSettings("RAW Lab", "Pathview+")
        return {key: settings.value(key) for key in settings.allKeys()}
    except ImportError:
        try:
            return json.loads(settings_path().read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}


def save_settings(values: dict) -> None:
    try:
        from PySide6.QtCore import QSettings

        settings = QSettings("RAW Lab", "Pathview+")
        for key, value in values.items():
            settings.setValue(key, value)
        settings.sync()
    except ImportError:
        settings_path().write_text(json.dumps(values, indent=2), encoding="utf-8")
