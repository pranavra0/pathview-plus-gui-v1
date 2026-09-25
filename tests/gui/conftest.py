from __future__ import annotations

import os

import pytest


@pytest.fixture(scope="session")
def qapp():
    """Create one offscreen QApplication without requiring pytest-qt."""
    pytest.importorskip("PySide6")
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    yield app
    app.processEvents()
