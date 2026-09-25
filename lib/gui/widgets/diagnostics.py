"""Structured mapping diagnostics presentation."""

from __future__ import annotations

import csv

try:
    from PySide6.QtWidgets import (
        QFileDialog,
        QHBoxLayout,
        QPlainTextEdit,
        QPushButton,
        QTableWidget,
        QTableWidgetItem,
        QVBoxLayout,
        QWidget,
    )

    _QT = True
except ImportError:
    _QT = False


if _QT:

    class DiagnosticsWidget(QWidget):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.text = QPlainTextEdit()
            self.text.setReadOnly(True)
            self.unmapped = QTableWidget(0, 2)
            self.unmapped.setHorizontalHeaderLabels(["Data class", "Identifier"])
            self.copy_button = QPushButton("Copy")
            self.save_button = QPushButton("Save unmapped IDs as CSV")
            buttons = QHBoxLayout()
            buttons.addWidget(self.copy_button)
            buttons.addWidget(self.save_button)
            buttons.addStretch()
            layout = QVBoxLayout(self)
            layout.addWidget(self.text)
            layout.addWidget(self.unmapped)
            layout.addLayout(buttons)
            self.copy_button.clicked.connect(self.text.copy)
            self.save_button.clicked.connect(self._save)

        def show_diagnostics(self, data):
            lines: list[str] = []
            known = {
                "species",
                "pathway",
                "nodes",
                "edges",
                "renderer",
                "output_file",
                "glyphs",
                "arcs",
                "compartments",
                "language",
                "source_file",
            }
            for key in known:
                if key in data:
                    lines.append(f"{key.replace('_', ' ').title()}: {data[key]}")
            for label, key in (("Genes", "gene_detail"), ("Compounds", "cpd_detail")):
                detail = data.get(key)
                if isinstance(detail, dict):
                    lines.extend(
                        (
                            label,
                            f"  Input identifiers: {detail.get('n_ids_input', 0)}",
                            f"  Identifiers used: {detail.get('n_ids_mapped', 0)}",
                            f"  Pathway nodes: {detail.get('n_nodes', 0)}",
                            f"  Nodes carrying data: {detail.get('n_nodes_with_data', 0)}",
                            f"  Mapping rate: {detail.get('mapped_fraction', 0):.1%}",
                            f"  Conditions: {len(detail.get('value_columns', []))}",
                        )
                    )
            for key, value in data.items():
                if key not in known and key not in {
                    "gene_detail",
                    "cpd_detail",
                    "unmapped_ids",
                }:
                    lines.append(f"{key}: {value}")
            self.text.setPlainText("\n".join(lines) or "No diagnostics available.")
            rows = []
            for key, label in (("gene_detail", "Genes"), ("cpd_detail", "Compounds")):
                rows.extend(
                    (label, str(identifier))
                    for identifier in data.get(key, {}).get("unmapped_ids", [])
                )
            self.unmapped.setRowCount(len(rows))
            for row, (label, identifier) in enumerate(rows):
                self.unmapped.setItem(row, 0, QTableWidgetItem(label))
                self.unmapped.setItem(row, 1, QTableWidgetItem(identifier))

        def toPlainText(self):
            return self.text.toPlainText()

        def _save(self):
            path, _ = QFileDialog.getSaveFileName(
                self, "Save unmapped identifiers", "unmapped.csv", "CSV (*.csv)"
            )
            if not path:
                return
            with open(path, "w", newline="", encoding="utf-8") as handle:
                writer = csv.writer(handle)
                writer.writerow(["data_class", "identifier"])
                for row in range(self.unmapped.rowCount()):
                    writer.writerow(
                        [
                            self.unmapped.item(row, 0).text(),
                            self.unmapped.item(row, 1).text(),
                        ]
                    )
else:

    class DiagnosticsWidget:
        def __init__(self, *args, **kwargs):
            raise ImportError(
                'PySide6 is required for GUI. Install with: pip install "pathview-plus[gui]"'
            )
