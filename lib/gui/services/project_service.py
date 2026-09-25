"""Safe JSON project persistence; scientific settings stay out of QSettings."""

from __future__ import annotations

import json
from pathlib import Path

from ..models import AppState

SCHEMA_VERSION = 1


def save_project(state: AppState, path: str | Path) -> Path:
    target = Path(path)
    if not target.name.endswith(".pvp.json"):
        target = target.with_name(target.name + ".pvp.json")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(state.to_dict(), indent=2), encoding="utf-8")
    state.project_path = target
    state.dirty = False
    return target


def load_project(path: str | Path) -> AppState:
    target = Path(path)
    try:
        payload = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"Could not read project file {target}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError("Project file must contain a JSON object.")
    version = payload.get("schema_version", SCHEMA_VERSION)
    if not isinstance(version, int) or version < 1:
        raise ValueError(f"Unsupported project schema version {version!r}.")
    # v1 files are data-only JSON. Unknown future fields are ignored; this is
    # safer than dropping a user's configuration merely because a newer GUI
    # added a display preference.
    state = AppState.from_dict(payload)
    state.project_path = target
    state.dirty = False
    for data in (
        state.kegg_config.gene,
        state.kegg_config.compound,
        state.sbgn_config.gene,
        state.sbgn_config.compound,
    ):
        if data.path and not data.path.exists():
            data.enabled = False
    return state


__all__ = ["SCHEMA_VERSION", "save_project", "load_project"]
