"""KEGG and offline SBGN pathway selection widgets."""

from __future__ import annotations

try:
    from PySide6.QtCore import Qt, QTimer, Signal
    from PySide6.QtWidgets import (
        QComboBox,
        QFileDialog,
        QFormLayout,
        QLabel,
        QLineEdit,
        QListWidget,
        QListWidgetItem,
        QPushButton,
        QTableWidget,
        QTableWidgetItem,
        QVBoxLayout,
        QWidget,
    )

    from ..services.pathway_service import (
        add_local_sbgn,
        parse_kegg_ids,
        search_sbgn,
        species_search,
    )

    _QT = True
except ImportError:
    _QT = False


if _QT:

    class PathwaySelector(QWidget):
        queue_changed = Signal()
        species_changed = Signal(str)

        def __init__(self, parent=None):
            super().__init__(parent)
            self.database = QComboBox()
            self.database.addItems(["kegg", "sbgn"])
            self.species = QLineEdit("hsa")
            self.species.setPlaceholderText("human, hsa, or 9606")
            self.species_results = QListWidget()
            self.species_results.setMaximumHeight(90)
            self.ids = QLineEdit()
            self.ids.setPlaceholderText("04110, 04010, or hsa04110")
            self.kegg_queue = QListWidget()
            self.kegg_queue.setSelectionMode(QListWidget.SingleSelection)
            self.source = QComboBox()
            self.source.addItem("All", "")
            try:
                from pathview import SBGN_SOURCES

                for key, name in SBGN_SOURCES.items():
                    self.source.addItem(name, key)
            except ImportError:
                pass
            self.search = QLineEdit()
            self.search.setPlaceholderText("Search bundled SBGN catalog")
            self.search_results = QTableWidget(0, 3)
            self.search_results.setHorizontalHeaderLabels(
                ["Pathway ID", "Source", "Filename"]
            )
            self.search_results.setSelectionBehavior(QTableWidget.SelectRows)
            self.search_results.setSelectionMode(QTableWidget.ExtendedSelection)
            self.add_button = QPushButton("Add selected to render queue")
            self.local_button = QPushButton("Open local .sbgn file…")
            self.queue = QListWidget()
            self.remove_button = QPushButton("Remove selected")
            self.clear_button = QPushButton("Clear all")
            self.up_button = QPushButton("Move up")
            self.down_button = QPushButton("Move down")
            self.select_all_button = QPushButton("Select all")
            self.up_button_sbgn = QPushButton("Move up")
            self.down_button_sbgn = QPushButton("Move down")
            self.select_all_button_sbgn = QPushButton("Select all")
            self.kegg_panel = QWidget()
            kform = QFormLayout(self.kegg_panel)
            kform.addRow("Species", self.species)
            kform.addRow("Suggestions", self.species_results)
            kform.addRow("Pathway IDs", self.ids)
            kform.addRow("Render queue", self.kegg_queue)
            kform.addRow("", self.up_button)
            kform.addRow("", self.down_button)
            kform.addRow("", self.select_all_button)
            self.sbgn_panel = QWidget()
            sform = QFormLayout(self.sbgn_panel)
            sform.addRow("Source", self.source)
            sform.addRow("Search", self.search)
            sform.addRow("Catalog results", self.search_results)
            sform.addRow("", self.add_button)
            sform.addRow("", self.local_button)
            sform.addRow("Render queue", self.queue)
            sform.addRow("", self.remove_button)
            sform.addRow("", self.clear_button)
            sform.addRow("", self.up_button_sbgn)
            sform.addRow("", self.down_button_sbgn)
            sform.addRow("", self.select_all_button_sbgn)
            layout = QVBoxLayout(self)
            layout.addWidget(QLabel("Pathway mode"))
            layout.addWidget(self.database)
            layout.addWidget(self.kegg_panel)
            layout.addWidget(self.sbgn_panel)
            self._timer = QTimer(self)
            self._timer.setSingleShot(True)
            self._timer.setInterval(250)
            self._timer.timeout.connect(self._search_species)
            self._catalog_timer = QTimer(self)
            self._catalog_timer.setSingleShot(True)
            self._catalog_timer.setInterval(250)
            self._catalog_timer.timeout.connect(self._search_catalog)
            self.database.currentTextChanged.connect(self._mode_changed)
            self.species.textChanged.connect(lambda _: self._timer.start())
            self.species_results.itemClicked.connect(self._choose_species)
            self.ids.editingFinished.connect(self._normalise_kegg)
            self.search.textChanged.connect(lambda _: self._catalog_timer.start())
            self.source.currentIndexChanged.connect(lambda _: self._catalog_timer.start())
            self.add_button.clicked.connect(self._add_selected)
            self.local_button.clicked.connect(self._open_local)
            self.remove_button.clicked.connect(
                lambda: self.queue.takeItem(self.queue.currentRow())
            )
            self.clear_button.clicked.connect(self.queue.clear)
            self.up_button.clicked.connect(lambda: self._move(self.kegg_queue, -1))
            self.down_button.clicked.connect(lambda: self._move(self.kegg_queue, 1))
            self.select_all_button.clicked.connect(lambda: self.kegg_queue.selectAll())
            self.up_button_sbgn.clicked.connect(lambda: self._move(self.queue, -1))
            self.down_button_sbgn.clicked.connect(lambda: self._move(self.queue, 1))
            self.select_all_button_sbgn.clicked.connect(lambda: self.queue.selectAll())
            self.kegg_queue.itemSelectionChanged.connect(self.queue_changed)
            self.queue.itemSelectionChanged.connect(self.queue_changed)
            self._mode_changed(self.database.currentText())

        def _move(self, widget, delta):
            row = widget.currentRow()
            target = row + delta
            if row < 0 or target < 0 or target >= widget.count():
                return
            item = widget.takeItem(row)
            widget.insertItem(target, item)
            widget.setCurrentRow(target)
            self.queue_changed.emit()

        def _mode_changed(self, mode: str):
            is_kegg = mode == "kegg"
            self.kegg_panel.setVisible(is_kegg)
            self.sbgn_panel.setVisible(not is_kegg)
            self.queue_changed.emit()

        def _search_species(self):
            self.species_results.clear()
            try:
                hits = species_search(self.species.text(), limit=10)
                for row in hits.iter_rows(named=True):
                    item = QListWidgetItem(
                        f"{row['kegg_code']}   {row['scientific_name']} ({row.get('common_name') or ''})"
                    )
                    item.setData(Qt.UserRole, row["kegg_code"])
                    self.species_results.addItem(item)
            except Exception:
                pass

        def _choose_species(self, item):
            code = item.data(Qt.UserRole)
            self.species.setText(code)
            self.species_results.clear()
            self.species_changed.emit(code)

        def _normalise_kegg(self):
            try:
                ids = parse_kegg_ids(self.ids.text())
                self.kegg_queue.clear()
                self.kegg_queue.addItems(ids)
                self.queue_changed.emit()
            except ValueError as exc:
                self.ids.setToolTip(str(exc))

        def _search_catalog(self):
            try:
                source = self.source.currentData() or None
                hits = search_sbgn(source, self.search.text(), limit=100)
                self.search_results.setRowCount(hits.height)
                for r, row in enumerate(hits.iter_rows(named=True)):
                    for c, key in enumerate(("pathway_id", "source", "filename")):
                        self.search_results.setItem(r, c, QTableWidgetItem(str(row[key])))
            except Exception:
                self.search_results.setRowCount(0)

        def _add_selected(self):
            for item in self.search_results.selectedItems():
                row = item.row()
                pathway = self.search_results.item(row, 0).text()
                if not self.queue.findItems(pathway, Qt.MatchExactly):
                    self.queue.addItem(pathway)
            self.queue_changed.emit()

        def _open_local(self):
            path, _ = QFileDialog.getOpenFileName(
                self, "Open SBGN file", "", "SBGN (*.sbgn)"
            )
            if path:
                self.add_local_path(path)

        def add_local_path(self, path: str):
            local = add_local_sbgn(path)
            text = f"Local    {local}"
            if not self.queue.findItems(text, Qt.MatchExactly):
                self.queue.addItem(text)
            self.queue_changed.emit()

        def values(self) -> list[str]:
            if self.database.currentText() == "kegg":
                return [
                    self.kegg_queue.item(i).text() for i in range(self.kegg_queue.count())
                ]
            return [
                self.queue.item(i).text().removeprefix("Local    ")
                for i in range(self.queue.count())
            ]
else:

    class PathwaySelector:
        def __init__(self, *args, **kwargs):
            raise ImportError(
                'PySide6 is required for GUI. Install with: pip install "pathview-plus[gui]"'
            )
