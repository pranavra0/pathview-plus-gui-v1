"""Gene and compound input card with bounded inspection and drag/drop."""

from __future__ import annotations

try:
    from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt, Signal
    from PySide6.QtWidgets import (
        QCheckBox,
        QComboBox,
        QFileDialog,
        QFormLayout,
        QLabel,
        QMessageBox,
        QPushButton,
        QWidget,
    )

    from pathview import supported_cpd_idtypes, supported_gene_idtypes

    from ..services.input_service import inspect_table
    from .drop_line_edit import DropLineEdit

    _QT = True

    class QTableModel(QAbstractTableModel):
        def __init__(self, frame):
            super().__init__()
            self.frame = frame

        def rowCount(self, parent=QModelIndex()):
            return self.frame.height

        def columnCount(self, parent=QModelIndex()):
            return self.frame.width

        def data(self, index, role=Qt.DisplayRole):
            if role == Qt.DisplayRole and index.isValid():
                return str(self.frame[index.row(), index.column()])
            return None

        def headerData(self, section, orientation, role=Qt.DisplayRole):
            if role == Qt.DisplayRole:
                return (
                    self.frame.columns[section]
                    if orientation == Qt.Horizontal
                    else str(section + 1)
                )
            return None
except ImportError:
    _QT = False


if _QT:

    class DataInputCard(QWidget):
        changed = Signal()
        preview_requested = Signal(object)

        def __init__(self, label: str, kind: str = "gene", parent=None):
            super().__init__(parent)
            self.kind = kind
            self.enabled = QCheckBox("Enable")
            self.enabled.setChecked(False)
            self.path = DropLineEdit("Drop CSV/TSV/TAB/TXT here")
            self.browse = QPushButton("Browse…")
            self.preview_button = QPushButton("Preview data")
            self.identifier = QComboBox()
            values = supported_gene_idtypes() if kind == "gene" else supported_cpd_idtypes()
            self.identifier.addItems(values)
            self.identifier.setCurrentText("ENTREZ" if kind == "gene" else "KEGG")
            self.summary = QLabel("No file selected")
            self.summary.setWordWrap(True)
            self.warning = QLabel("")
            self.warning.setWordWrap(True)
            self.warning.setStyleSheet("color: #9a6700")
            form = QFormLayout(self)
            form.addRow(label, self.enabled)
            form.addRow("File", self.path)
            form.addRow("", self.browse)
            form.addRow("Identifier type", self.identifier)
            form.addRow("Summary", self.summary)
            form.addRow("", self.warning)
            form.addRow("", self.preview_button)
            self.browse.clicked.connect(self._browse)
            self.path.path_dropped.connect(self._path_changed)
            self.path.editingFinished.connect(self._path_changed)
            self.enabled.toggled.connect(self.changed)
            self.identifier.currentTextChanged.connect(lambda _: self.changed.emit())
            self.preview_button.clicked.connect(self._preview)
            self._path_changed()

        def _browse(self):
            path, _ = QFileDialog.getOpenFileName(
                self, "Select molecular data", "", "Data (*.csv *.tsv *.tab *.txt)"
            )
            if path:
                self.path.setText(path)
                self._path_changed()

        def _path_changed(self, *_):
            path = self.path.text().strip()
            if not path:
                self.summary.setText("No file selected")
                self.warning.clear()
                self.changed.emit()
                return
            try:
                info = inspect_table(path)
                ignored = ", ".join(info["ignored_columns"]) or "none"
                self.summary.setText(
                    f"{info['rows']:,} rows · {len(info['numeric_columns'])} conditions · "
                    f"Identifier: {info['id_column']}"
                )
                self.warning.setText(
                    f"Ignored nonnumeric columns: {ignored}"
                    if info["ignored_columns"]
                    else ""
                )
            except Exception as exc:
                self.summary.setText(f"Could not load file: {exc}")
                self.warning.clear()
            self.changed.emit()

        def _preview(self):
            try:
                self.preview_requested.emit(inspect_table(self.path.text()))
            except Exception as exc:
                QMessageBox.warning(self, "Could not preview data", str(exc))

        def file_path(self):
            return self.path.text().strip() or None

        def id_type(self):
            return self.identifier.currentText()
else:

    class DataInputCard:  # pragma: no cover - exercised only without GUI extras
        def __init__(self, *args, **kwargs):
            raise ImportError(
                'PySide6 is required for GUI. Install with: pip install "pathview-plus[gui]"'
            )
