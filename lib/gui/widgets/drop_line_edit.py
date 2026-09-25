from __future__ import annotations

try:
    from PySide6.QtCore import Signal
    from PySide6.QtWidgets import QLineEdit

    _QT = True
except ImportError:
    _QT = False


if _QT:

    class DropLineEdit(QLineEdit):
        path_dropped = Signal(str)

        def __init__(self, placeholder: str = "", parent=None):
            super().__init__(parent)
            self.setPlaceholderText(placeholder)
            self.setAcceptDrops(True)

        def dragEnterEvent(self, event):
            urls = event.mimeData().urls()
            if urls and urls[0].isLocalFile():
                event.acceptProposedAction()
            else:
                event.ignore()

        def dropEvent(self, event):
            urls = event.mimeData().urls()
            if not urls or not urls[0].isLocalFile():
                event.ignore()
                return
            path = urls[0].toLocalFile()
            if path.lower().endswith((".csv", ".tsv", ".tab", ".txt", ".sbgn")):
                self.setText(path)
                self.path_dropped.emit(path)
                event.acceptProposedAction()
            else:
                event.ignore()
else:

    class DropLineEdit:
        def __init__(self, *args, **kwargs):
            raise ImportError(
                'PySide6 is required for GUI. Install with: pip install "pathview-plus[gui]"'
            )
