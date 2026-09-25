from __future__ import annotations

try:
    from PySide6.QtCore import QUrl, Signal
    from PySide6.QtGui import QDesktopServices
    from PySide6.QtWidgets import QApplication, QMenu, QTableWidget, QTableWidgetItem

    _QT = True
except ImportError:
    _QT = False


if _QT:

    class ResultsTable(QTableWidget):
        result_selected = Signal(object)

        def __init__(self, parent=None):
            super().__init__(0, 5, parent)
            self.setHorizontalHeaderLabels(
                ["Pathway", "Source", "Status", "Output", "Mapping"]
            )
            self.setSelectionBehavior(QTableWidget.SelectRows)
            self.setContextMenuPolicy(3)
            self.cellClicked.connect(self._selected)
            self.cellDoubleClicked.connect(self._open)
            self.customContextMenuRequested.connect(self._menu)
            self._results = []

        def add_result(self, result):
            self._results.append(result)
            row = self.rowCount()
            self.insertRow(row)
            diagnostics = getattr(result, "diagnostics", {}) or {}
            mapping = ""
            for label, key in (("Gene", "gene_detail"), ("Compound", "cpd_detail")):
                detail = diagnostics.get(key)
                if detail:
                    mapping += (
                        (" • " if mapping else "")
                        + f"{label} {detail.get('n_nodes_with_data', 0)}/{detail.get('n_nodes', 0)}"
                    )
            values = (
                result.pathway,
                result.source,
                result.status,
                str(result.output_path or result.error or ""),
                mapping,
            )
            for col, value in enumerate(values):
                self.setItem(row, col, QTableWidgetItem(value))

        def _selected(self, row, _column):
            if 0 <= row < len(self._results):
                self.result_selected.emit(self._results[row])

        def _open(self, row, column):
            if 0 <= row < len(self._results) and self._results[row].output_path:
                QDesktopServices.openUrl(
                    QUrl.fromLocalFile(str(self._results[row].output_path))
                )

        def _menu(self, pos):
            row = self.rowAt(pos.y())
            if row < 0 or row >= len(self._results):
                return
            result = self._results[row]
            menu = QMenu(self)
            open_action = menu.addAction("Open")
            folder_action = menu.addAction("Open containing folder")
            copy_action = menu.addAction("Copy output path")
            selected = menu.exec(self.viewport().mapToGlobal(pos))
            if selected == open_action:
                self._open(row, 0)
            elif selected == folder_action and result.output_path:
                QDesktopServices.openUrl(QUrl.fromLocalFile(str(result.output_path.parent)))
            elif selected == copy_action and result.output_path:
                QApplication.clipboard().setText(str(result.output_path))
else:

    class ResultsTable:
        def __init__(self, *args, **kwargs):
            raise ImportError(
                'PySide6 is required for GUI. Install with: pip install "pathview-plus[gui]"'
            )
