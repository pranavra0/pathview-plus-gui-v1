"""Optional Pathview+ Qt desktop application. Importing this package never imports Qt."""

from .models import AppState, RenderConfig, RunResult, validate_config

__all__ = ["AppState", "RenderConfig", "RunResult", "validate_config"]
