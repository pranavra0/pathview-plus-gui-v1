from __future__ import annotations


def test_preview_loads_a_generated_png(qapp, tmp_path):
    from pathview.gui.widgets.preview import PreviewWidget
    from PySide6.QtGui import QColor, QImage

    image_path = tmp_path / "preview.png"
    image = QImage(12, 8, QImage.Format.Format_RGB32)
    image.fill(QColor("#336699"))
    assert image.save(str(image_path))

    widget = PreviewWidget()
    widget.show_path(image_path)
    qapp.processEvents()

    assert not widget.label.pixmap().isNull()
