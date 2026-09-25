"""Qt presentation layer for the Pathview+ desktop workflow."""

from __future__ import annotations

import logging
from pathlib import Path

from .models import AppState, DataConfig, RenderConfig, validate_config
from .services.project_service import load_project, save_project
from .workers import RenderWorker

log = logging.getLogger("pathview.gui")

try:
    from PySide6.QtCore import QObject, QSettings, Qt, QUrl, Signal
    from PySide6.QtGui import QAction, QDesktopServices
    from PySide6.QtWidgets import (
        QFileDialog,
        QLabel,
        QMainWindow,
        QMessageBox,
        QProgressBar,
        QSplitter,
        QStatusBar,
        QTabWidget,
        QTextEdit,
        QVBoxLayout,
        QWidget,
    )

    from .widgets.advanced_panel import AdvancedPanel
    from .widgets.appearance_panel import AppearancePanel
    from .widgets.data_input import DataInputCard
    from .widgets.diagnostics import DiagnosticsWidget
    from .widgets.pathway_selector import PathwaySelector
    from .widgets.preview import PreviewWidget
    from .widgets.results_table import ResultsTable

    _QT = True
except ImportError:
    _QT = False


if _QT:

    class _Bridge(QObject):
        result = Signal(object)
        done = Signal()
        started = Signal()
        pathway_started = Signal(int, int, str)

    class MainWindow(QMainWindow):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.setWindowTitle("Pathview+")
            self.setMinimumSize(1100, 700)
            self.resize(1400, 900)
            self.state = AppState()
            self.worker = None
            self.bridge = _Bridge(self)
            self.bridge.result.connect(self._show_result)
            self.bridge.done.connect(self._render_done)
            self.bridge.pathway_started.connect(self._pathway_started)
            self._build_ui()
            self._build_menus()
            self._restore_settings()
            self._log("Ready. Load molecular data and choose a pathway to begin.")

        def _build_ui(self):
            self.data_gene = DataInputCard("Gene / protein data", "gene")
            self.data_cpd = DataInputCard("Compound / metabolite data", "compound")
            self.pathways = PathwaySelector()
            self.appearance = AppearancePanel()
            self.advanced = AdvancedPanel()
            tabs = QTabWidget()
            data_page = QWidget()
            data_layout = QVBoxLayout(data_page)
            data_layout.addWidget(self.data_gene)
            data_layout.addWidget(self.data_cpd)
            data_layout.addStretch()
            tabs.addTab(data_page, "Data")
            tabs.addTab(self.pathways, "Pathway")
            tabs.addTab(self.appearance, "Appearance")
            tabs.addTab(self.advanced, "Advanced")
            self.render_button = self._button("Render")
            self.cancel_button = self._button("Cancel after current")
            self.cancel_button.setEnabled(False)
            output_label = QLabel("Output directory")
            self.output_dir = self._line_edit(str(Path.cwd()))
            self.output_browse = self._button("Browse…")
            left = QWidget()
            left_layout = QVBoxLayout(left)
            left_layout.addWidget(tabs)
            left_layout.addWidget(output_label)
            left_layout.addWidget(self.output_dir)
            left_layout.addWidget(self.output_browse)
            left_layout.addWidget(self.render_button)
            left_layout.addWidget(self.cancel_button)
            self.preview = PreviewWidget()
            self.results = ResultsTable()
            self.diagnostics = DiagnosticsWidget()
            self.log_view = QTextEdit()
            self.log_view.setReadOnly(True)
            bottom = QTabWidget()
            bottom.addTab(self.results, "Results")
            bottom.addTab(self.diagnostics, "Diagnostics")
            bottom.addTab(self.log_view, "Log")
            self.top_split = QSplitter(Qt.Horizontal)
            self.top_split.addWidget(left)
            self.top_split.addWidget(self.preview)
            self.top_split.setStretchFactor(1, 1)
            self.main_split = QSplitter(Qt.Vertical)
            self.main_split.addWidget(self.top_split)
            self.main_split.addWidget(bottom)
            self.main_split.setStretchFactor(0, 4)
            self.main_split.setStretchFactor(1, 1)
            self.setCentralWidget(self.main_split)
            self.progress = QProgressBar()
            self.progress.setRange(0, 1)
            self.status = QStatusBar()
            self.setStatusBar(self.status)
            self.status.addPermanentWidget(self.progress)
            self.render_button.clicked.connect(self.start_render)
            self.cancel_button.clicked.connect(self.cancel_render)
            self.output_browse.clicked.connect(self._choose_output)
            self.pathways.database.currentTextChanged.connect(self._mode_changed)
            self.pathways.queue_changed.connect(self._mark_dirty)
            for card in (self.data_gene, self.data_cpd):
                card.changed.connect(self._mark_dirty)
                card.preview_requested.connect(self._show_data_preview)
            self.results.result_selected.connect(self._select_result)
            self._mode_changed(self.pathways.database.currentText())
            self.advanced.offline.toggled.connect(self._offline_changed)

        def _button(self, text):
            from PySide6.QtWidgets import QPushButton

            return QPushButton(text)

        def _line_edit(self, text):
            from PySide6.QtWidgets import QLineEdit

            return QLineEdit(text)

        def _mode_changed(self, mode):
            self.state.current_mode = mode
            self.state.dirty = True
            is_kegg = mode == "kegg"
            for widget in (
                self.advanced.mode,
                self.advanced.split_group,
                self.advanced.expand_node,
                self.advanced.link_edges,
                self.advanced.min_nodes,
                self.advanced.map_symbol,
            ):
                widget.setVisible(is_kegg)
            for widget in (
                self.advanced.show_compartments,
                self.advanced.show_processes,
                self.advanced.overwrite,
            ):
                widget.setVisible(not is_kegg)
            if mode == "sbgn":
                self.state.sbgn_config.gene.id_type = "SYMBOL"

        def _offline_changed(self, enabled):
            from pathview.cache import set_offline

            set_offline(enabled)
            self.state.offline = enabled
            self._log("Offline mode enabled" if enabled else "Offline mode disabled")

        def _mark_dirty(self):
            self.state.dirty = True

        def _choose_output(self):
            path = QFileDialog.getExistingDirectory(
                self, "Select output directory", self.output_dir.text()
            )
            if path:
                self.output_dir.setText(path)
                self._mark_dirty()

        def _config_from_widgets(self) -> RenderConfig:
            mode = self.pathways.database.currentText()
            config = self.state.sbgn_config if mode == "sbgn" else self.state.kegg_config
            config.mode = mode
            config.pathways = self.pathways.values()
            config.species = self.pathways.species.text().strip()
            config.output_dir = Path(self.output_dir.text().strip() or ".")
            config.gene = DataConfig(
                Path(self.data_gene.file_path()) if self.data_gene.file_path() else None,
                self.data_gene.id_type(),
                self.data_gene.enabled.isChecked(),
            )
            config.compound = DataConfig(
                Path(self.data_cpd.file_path()) if self.data_cpd.file_path() else None,
                self.data_cpd.id_type(),
                self.data_cpd.enabled.isChecked(),
            )
            config.output_format = self.appearance.format.currentText()
            config.theme = self.appearance.theme.currentText()
            config.title = self.appearance.title.text() or None
            config.subtitle = self.appearance.subtitle.text() or None
            config.figure_width = self.appearance.width.value()
            config.dpi = self.appearance.dpi.value()
            config.map_without_data = self.advanced.map_null.isChecked()
            config.extra.update(
                {
                    "render_mode": self.advanced.mode.currentText(),
                    "node_sum": self.advanced.node_sum.currentText(),
                    "plot_col_key": self.appearance.show_key.isChecked(),
                    "draw_edges": self.advanced.edges.isChecked(),
                    "show_link_edges": self.advanced.link_edges.isChecked(),
                    "split_group": self.advanced.split_group.isChecked(),
                    "expand_node": self.advanced.expand_node.isChecked(),
                    "map_symbol": self.advanced.map_symbol.isChecked(),
                    "map_cpd_name": self.advanced.map_cpd_name.isChecked(),
                    "show_compartments": self.advanced.show_compartments.isChecked(),
                    "show_processes": self.advanced.show_processes.isChecked(),
                    "overwrite": self.advanced.overwrite.isChecked(),
                    "min_nnodes": self.advanced.min_nodes.value(),
                    "kegg_dir": str(Path.home() / ".cache" / "pathview-plus"),
                    "sbgn_dir": str(Path.home() / ".cache" / "pathview-plus"),
                }
            )
            config.gene_scale.palette = self.appearance.gene_palette.currentText()
            config.gene_scale.limit = self.appearance.gene_limit.value()
            config.gene_scale.bins = self.appearance.gene_bins.value()
            config.compound_scale.palette = self.appearance.cpd_palette.currentText()
            config.compound_scale.limit = self.appearance.cpd_limit.value()
            config.compound_scale.bins = self.appearance.cpd_bins.value()
            seed = self.advanced.seed.text().strip()
            config.extra["rand_seed"] = seed or None
            config.offline = self.advanced.offline.isChecked()
            self.state.offline = config.offline
            return config.copy()

        def _apply_state_to_widgets(self):
            config = self.state.config
            self.pathways.database.setCurrentText(config.mode)
            self.pathways.species.setText(config.species)
            self.pathways.kegg_queue.clear()
            self.pathways.queue.clear()
            if config.mode == "kegg":
                self.pathways.kegg_queue.addItems([str(p) for p in config.pathways])
            else:
                self.pathways.queue.addItems([str(p) for p in config.pathways])
            for card, data in (
                (self.data_gene, config.gene),
                (self.data_cpd, config.compound),
            ):
                card.path.setText(str(data.path) if data.path else "")
                card.enabled.setChecked(data.enabled)
                card.identifier.setCurrentText(data.id_type)
                card._path_changed()
            self.output_dir.setText(str(config.output_dir))
            self.appearance.theme.setCurrentText(config.theme)
            self.appearance.format.setCurrentText(config.output_format)
            self.appearance.title.setText(config.title or "")
            self.appearance.subtitle.setText(config.subtitle or "")
            self.appearance.width.setValue(config.figure_width)
            self.appearance.dpi.setValue(config.dpi)
            self.appearance.gene_palette.setCurrentText(config.gene_scale.palette)
            self.appearance.gene_limit.setValue(config.gene_scale.limit)
            self.appearance.gene_bins.setValue(config.gene_scale.bins)
            self.appearance.cpd_palette.setCurrentText(config.compound_scale.palette)
            self.appearance.cpd_limit.setValue(config.compound_scale.limit)
            self.appearance.cpd_bins.setValue(config.compound_scale.bins)
            self.advanced.mode.setCurrentText(config.extra.get("render_mode", "auto"))
            self.advanced.node_sum.setCurrentText(config.extra.get("node_sum", "sum"))
            self.advanced.offline.setChecked(self.state.offline)
            self.results.setRowCount(0)
            self.state.dirty = False

        def start_render(self):
            config = self._config_from_widgets()
            errors = validate_config(config)
            if errors:
                self.status.showMessage("; ".join(errors))
                return
            self._set_busy(True)
            self.results.setRowCount(0)
            self.state.current_results.clear()
            self.progress.setRange(0, len(config.pathways))
            self.progress.setValue(0)
            self.worker = RenderWorker(
                config,
                on_result=lambda result: self.bridge.result.emit(result),
                on_done=lambda: self.bridge.done.emit(),
            )
            self.worker.start()
            self._log(f"Rendering {len(config.pathways)} pathway(s)")

        def cancel_render(self):
            if self.worker:
                self.worker.cancel()
                self.status.showMessage("Cancel requested; current pathway will finish")

        def _pathway_started(self, index, total, pathway):
            self.progress.setRange(0, total)
            self.progress.setValue(index)
            self.status.showMessage(f"Rendering {index + 1} of {total} — {pathway}")

        def _show_result(self, result):
            self.state.current_results.append(result)
            self.results.add_result(result)
            if result.output_path and result.status in {"success", "Succeeded"}:
                self.preview.show_path(result.output_path)
                self.diagnostics.show_diagnostics(result.diagnostics)
                self.progress.setValue(self.progress.value() + 1)
                self._log(f"Completed {result.pathway}: {result.output_path}")
            else:
                self._log(f"Failed {result.pathway}: {result.error or result.status}")
                if result.status not in {"cancelled", "Canceled"}:
                    self._show_error(result)
            for warning in result.warnings:
                self._log(f"Warning {result.pathway}: {warning}")

        def _show_error(self, result):
            message = result.error or "Unknown rendering error"
            titles = {
                "SpeciesNotFoundError": "Species not found",
                "PathwayNotFoundError": "Pathway not found",
                "NetworkError": "Network resource unavailable",
                "MappingError": "No molecular data mapped",
                "ParseError": "Could not parse pathway file",
                "RenderError": "Rendering failed",
            }
            title = next(
                (label for key, label in titles.items() if key in message),
                "Unexpected application error",
            )
            QMessageBox.warning(self, title, message)

        def _select_result(self, result):
            if result.output_path:
                self.preview.show_path(result.output_path)
            self.diagnostics.show_diagnostics(result.diagnostics)

        def _render_done(self):
            self._set_busy(False)
            self.status.showMessage("Render complete")

        def _set_busy(self, busy):
            self.render_button.setEnabled(not busy)
            self.cancel_button.setEnabled(busy)
            for widget in (
                self.pathways,
                self.data_gene,
                self.data_cpd,
                self.appearance,
                self.advanced,
                self.output_dir,
                self.output_browse,
            ):
                widget.setEnabled(not busy)

        def _log(self, message):
            self.log_view.append(message)

        def _show_data_preview(self, info):
            from PySide6.QtWidgets import QDialog, QTableView, QVBoxLayout

            from .widgets.data_input import QTableModel

            dialog = QDialog(self)
            dialog.setWindowTitle(f"Preview — {info['path']}")
            layout = QVBoxLayout(dialog)
            table = QTableView()
            layout.addWidget(table)
            table.setModel(QTableModel(info["preview"]))
            dialog.resize(800, 500)
            dialog.exec()

        def _build_menus(self):
            file_menu = self.menuBar().addMenu("File")
            self._action(file_menu, "New Project", self.new_project)
            self._action(file_menu, "Open Project…", self.open_project)
            self._action(file_menu, "Save Project", self.save_project)
            self._action(file_menu, "Save Project As…", self.save_project_as)
            file_menu.addSeparator()
            self._action(file_menu, "Exit", self.close)
            view = self.menuBar().addMenu("View")
            self._action(view, "Fit Preview", self.preview.fit)
            self._action(view, "Zoom In", lambda: self.preview.zoom(1.2))
            self._action(view, "Zoom Out", lambda: self.preview.zoom(1 / 1.2))
            self._action(view, "100%", self.preview.one_hundred)
            tools = self.menuBar().addMenu("Tools")
            self._action(
                tools,
                "Settings…",
                lambda: QMessageBox.information(
                    self,
                    "Settings",
                    "Use the output directory selector and Offline mode control.",
                ),
            )
            self._action(
                tools,
                "Open Cache Folder",
                lambda: QDesktopServices.openUrl(
                    QUrl.fromLocalFile(str(Path.home() / ".cache" / "pathview-plus"))
                ),
            )
            self._action(tools, "Clear HTTP Cache…", self.clear_cache)
            self._action(
                tools,
                "Offline Mode",
                lambda: self.advanced.offline.setChecked(
                    not self.advanced.offline.isChecked()
                ),
            )
            help_menu = self.menuBar().addMenu("Help")
            self._action(help_menu, "About Pathview+", self.about)

        def _action(self, menu, title, callback):
            action = QAction(title, self)
            action.triggered.connect(callback)
            menu.addAction(action)
            return action

        def clear_cache(self):
            from pathview.cache import clear_cache

            answer = QMessageBox.question(
                self,
                "Clear HTTP Cache",
                "Delete all Pathview+ cached HTTP resources?",
            )
            if answer == QMessageBox.Yes:
                removed = clear_cache()
                self._log(f"Removed {removed} cached files.")
                self.status.showMessage(f"Removed {removed} cached files.")

        def new_project(self):
            self.state = AppState()
            self._apply_state_to_widgets()
            self._log("New project")

        def open_project(self):
            path, _ = QFileDialog.getOpenFileName(
                self, "Open project", "", "Pathview+ project (*.pvp.json)"
            )
            if path:
                try:
                    self.state = load_project(path)
                    self._apply_state_to_widgets()
                    self._log(f"Opened {path}")
                except ValueError as exc:
                    QMessageBox.warning(self, "Could not open project", str(exc))

        def save_project(self):
            self._config_from_widgets()
            if self.state.project_path:
                save_project(self.state, self.state.project_path)
            else:
                self.save_project_as()

        def save_project_as(self):
            self._config_from_widgets()
            path, _ = QFileDialog.getSaveFileName(
                self, "Save project", "project.pvp.json", "Pathview+ project (*.pvp.json)"
            )
            if path:
                save_project(self.state, path)

        def about(self):
            import pathview

            QMessageBox.about(
                self,
                "About Pathview+",
                f"Pathview+ {pathview.__version__}\nKEGG and SBGN pathway visualization\nGUI: PySide6 / Qt",
            )

        def closeEvent(self, event):
            if self.worker and self.worker.running:
                self.worker.cancel()
                self.worker._thread.join(timeout=2)
            settings = QSettings("RAW Lab", "Pathview+")
            settings.setValue("geometry", self.saveGeometry())
            settings.setValue("windowState", self.saveState())
            settings.setValue("topSplitter", self.top_split.sizes())
            settings.setValue("mainSplitter", self.main_split.sizes())
            settings.sync()
            super().closeEvent(event)

        def _restore_settings(self):
            settings = QSettings("RAW Lab", "Pathview+")
            geometry = settings.value("geometry")
            state = settings.value("windowState")
            top_sizes = settings.value("topSplitter")
            main_sizes = settings.value("mainSplitter")
            if geometry:
                self.restoreGeometry(geometry)
            if state:
                self.restoreState(state)
            if top_sizes:
                self.top_split.setSizes([int(size) for size in top_sizes])
            if main_sizes:
                self.main_split.setSizes([int(size) for size in main_sizes])

    def create_window():
        return MainWindow()
else:

    class MainWindow:
        def __init__(self, *args, **kwargs):
            raise ImportError(
                'PySide6 is required for GUI. Install with: pip install "pathview-plus[gui]"'
            )

    def create_window():
        return MainWindow()
