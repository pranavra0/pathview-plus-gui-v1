from __future__ import annotations


def test_diagnostics_widget_displays_structured_fields(qapp):
    from pathview.gui.widgets.diagnostics import DiagnosticsWidget

    widget = DiagnosticsWidget()
    widget.show_diagnostics({"input_ids": 4, "mapped_ids": 3, "conditions": ["Control"]})

    text = widget.toPlainText()
    assert "input_ids: 4" in text
    assert "mapped_ids: 3" in text
    assert "Control" in text
