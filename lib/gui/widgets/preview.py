"""Actual-output preview with fit/zoom controls."""

from __future__ import annotations

try:
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QImage, QPixmap
    from PySide6.QtSvgWidgets import QSvgWidget
    from PySide6.QtWidgets import (
        QGraphicsPixmapItem,
        QGraphicsScene,
        QGraphicsView,
        QLabel,
        QPushButton,
        QToolBar,
        QVBoxLayout,
        QWidget,
    )

    _QT = True
except ImportError:
    _QT = False


if _QT:

    class PreviewWidget(QWidget):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.view = QGraphicsView()
            self.scene = QGraphicsScene(self.view)
            self.view.setScene(self.scene)
            self.view.setDragMode(QGraphicsView.ScrollHandDrag)
            self.label = QLabel()
            self.label.setAlignment(Qt.AlignCenter)
            self.label.hide()
            self.svg = QSvgWidget()
            self.svg.hide()
            self.pdf_label = QLabel()
            self.pdf_label.setAlignment(Qt.AlignCenter)
            self.pdf_label.hide()
            self.placeholder = QLabel("Render a pathway to preview it here.")
            self.placeholder.setAlignment(Qt.AlignCenter)
            toolbar = QToolBar()
            for text, callback in (
                ("Zoom in", lambda: self.zoom(1.2)),
                ("Zoom out", lambda: self.zoom(1 / 1.2)),
                ("Fit", self.fit),
                ("100%", self.one_hundred),
            ):
                button = QPushButton(text)
                button.clicked.connect(callback)
                toolbar.addWidget(button)
            layout = QVBoxLayout(self)
            layout.addWidget(toolbar)
            layout.addWidget(self.view)
            layout.addWidget(self.label)
            layout.addWidget(self.svg)
            layout.addWidget(self.pdf_label)
            layout.addWidget(self.placeholder)
            self._scale = 1.0
            self._image_item = None

        def _show_placeholder(self):
            self.view.hide()
            self.label.hide()
            self.svg.hide()
            self.pdf_label.hide()
            self.placeholder.show()

        def show_path(self, path):
            from pathlib import Path

            target = Path(path) if path else None
            if not target or not target.exists():
                self._show_placeholder()
                return
            self.placeholder.hide()
            if target.suffix.lower() == ".svg":
                self.view.hide()
                self.label.hide()
                self.pdf_label.hide()
                self.svg.show()
                self.svg.load(str(target))
                return
            if target.suffix.lower() == ".pdf":
                self.view.hide()
                self.label.hide()
                self.svg.hide()
                self.pdf_label.show()
                try:
                    from PySide6.QtPdf import QPdfDocument

                    doc = QPdfDocument(self)
                    doc.load(str(target))
                    size = doc.pagePointSize(0).toSize()
                    image = doc.render(0, size)
                    self.pdf_label.setPixmap(QPixmap.fromImage(image))
                except Exception:
                    self.pdf_label.setText(
                        f"PDF output: {target}\nOpen the file to inspect it."
                    )
                return
            image = QImage(str(target))
            self.label.setPixmap(QPixmap.fromImage(image))
            self.svg.hide()
            self.pdf_label.hide()
            self.view.show()
            self.scene.clear()
            self._image_item = QGraphicsPixmapItem(QPixmap.fromImage(image))
            self.scene.addItem(self._image_item)
            self.fit()

        def zoom(self, factor: float):
            if self.view.isVisible():
                self.view.scale(factor, factor)
                self._scale *= factor

        def fit(self):
            if self._image_item is not None:
                self.view.fitInView(self._image_item, Qt.KeepAspectRatio)
                self._scale = 1.0

        def one_hundred(self):
            if self._image_item is not None:
                self.view.resetTransform()
                self._scale = 1.0
else:

    class PreviewWidget:
        def __init__(self, *args, **kwargs):
            raise ImportError(
                'PySide6 is required for GUI. Install with: pip install "pathview-plus[gui]"'
            )
