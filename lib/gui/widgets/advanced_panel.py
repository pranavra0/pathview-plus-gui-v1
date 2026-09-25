from __future__ import annotations

try:
    from PySide6.QtWidgets import (
        QCheckBox,
        QComboBox,
        QFormLayout,
        QLineEdit,
        QSpinBox,
        QWidget,
    )

    _QT = True
except ImportError:
    _QT = False


if _QT:

    class AdvancedPanel(QWidget):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.mode = QComboBox()
            self.mode.addItems(["auto", "native", "vector", "graph", "svg"])
            self.node_sum = QComboBox()
            self.node_sum.addItems(
                ["sum", "mean", "median", "max", "min", "max_abs", "random", "first"]
            )
            self.seed = QLineEdit()
            self.seed.setPlaceholderText("Optional integer")
            self.split_group = QCheckBox("Split complexes into subunits")
            self.expand_node = QCheckBox("Expand multi-gene nodes")
            self.map_symbol = QCheckBox("Map gene symbols")
            self.map_symbol.setChecked(True)
            self.map_cpd_name = QCheckBox("Map compound names")
            self.map_cpd_name.setChecked(True)
            self.edges = QCheckBox("Draw edges")
            self.edges.setChecked(True)
            self.link_edges = QCheckBox("Include pathway-link edges")
            self.min_nodes = QSpinBox()
            self.min_nodes.setRange(0, 1_000_000)
            self.min_nodes.setValue(3)
            self.show_compartments = QCheckBox("Show compartments")
            self.show_compartments.setChecked(True)
            self.show_processes = QCheckBox("Show process glyphs")
            self.show_processes.setChecked(True)
            self.overwrite = QCheckBox("Re-download pathway file")
            self.map_null = QCheckBox("Render pathway without molecular data")
            self.offline = QCheckBox("Offline mode")
            self.mode.setToolTip(
                "Auto uses a cached native map when available, otherwise vector rendering."
            )
            self.node_sum.setToolTip(
                "Aggregation applied when multiple identifiers map to one pathway node."
            )
            form = QFormLayout(self)
            for label, widget in (
                ("KEGG render mode", self.mode),
                ("Node aggregation", self.node_sum),
                ("Random seed", self.seed),
                ("Minimum positioned nodes", self.min_nodes),
            ):
                form.addRow(label, widget)
            for widget in (
                self.split_group,
                self.expand_node,
                self.map_symbol,
                self.map_cpd_name,
                self.edges,
                self.link_edges,
                self.show_compartments,
                self.show_processes,
                self.overwrite,
                self.map_null,
                self.offline,
            ):
                form.addRow("", widget)
            self.node_sum.currentTextChanged.connect(
                lambda value: self.seed.setEnabled(value == "random")
            )
            self.seed.setEnabled(False)
else:

    class AdvancedPanel:
        def __init__(self, *args, **kwargs):
            raise ImportError(
                'PySide6 is required for GUI. Install with: pip install "pathview-plus[gui]"'
            )
