from __future__ import annotations


def test_main_window_opens_with_workflow_controls(qapp):
    from pathview.gui.main_window import create_window

    window = create_window()
    window.show()
    qapp.processEvents()

    assert window.windowTitle() == "Pathview+"
    assert window.minimumWidth() >= 1100
    assert window.minimumHeight() >= 700
    assert window.render_button.text() == "Render"
    assert window.cancel_button.isEnabled() is False
    assert window.pathways.database.currentText() == "kegg"

    window.close()
