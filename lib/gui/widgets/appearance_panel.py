from __future__ import annotations

try:
    from PySide6.QtWidgets import (
        QCheckBox,
        QComboBox,
        QDoubleSpinBox,
        QFormLayout,
        QLineEdit,
        QSpinBox,
        QWidget,
    )

    from pathview import THEMES, list_palettes

    _QT = True
except ImportError:
    _QT = False


if _QT:

    class AppearancePanel(QWidget):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.theme = QComboBox()
            self.theme.addItems(list(THEMES) or ["publication", "slate", "dark"])
            self.format = QComboBox()
            self.format.addItems(["png", "pdf", "svg"])
            self.title = QLineEdit()
            self.subtitle = QLineEdit()
            self.width = QDoubleSpinBox()
            self.width.setRange(1, 100)
            self.width.setDecimals(1)
            self.width.setValue(14.0)
            self.dpi = QSpinBox()
            self.dpi.setRange(72, 600)
            self.dpi.setValue(220)
            self.show_key = QCheckBox("Show color key")
            self.show_key.setChecked(True)
            self.gene_palette = QComboBox()
            self.gene_palette.addItems(sorted(list_palettes()))
            self.cpd_palette = QComboBox()
            self.cpd_palette.addItems(sorted(list_palettes()))
            self.gene_limit = QDoubleSpinBox()
            self.gene_limit.setRange(0.000001, 1_000_000)
            self.gene_limit.setValue(1.0)
            self.cpd_limit = QDoubleSpinBox()
            self.cpd_limit.setRange(0.000001, 1_000_000)
            self.cpd_limit.setValue(1.0)
            self.gene_bins = QSpinBox()
            self.gene_bins.setRange(1, 100)
            self.gene_bins.setValue(10)
            self.cpd_bins = QSpinBox()
            self.cpd_bins.setRange(1, 100)
            self.cpd_bins.setValue(10)
            form = QFormLayout(self)
            for label, widget in (
                ("Theme", self.theme),
                ("Output format", self.format),
                ("Title", self.title),
                ("Subtitle", self.subtitle),
                ("Figure width", self.width),
                ("DPI", self.dpi),
                ("Gene palette", self.gene_palette),
                ("Gene limit", self.gene_limit),
                ("Gene bins", self.gene_bins),
                ("Compound palette", self.cpd_palette),
                ("Compound limit", self.cpd_limit),
                ("Compound bins", self.cpd_bins),
            ):
                form.addRow(label, widget)
            form.addRow("", self.show_key)
            self.gene_palette.setToolTip(
                "Low / mid / high colors for gene or protein values."
            )
            self.cpd_palette.setToolTip(
                "Independent low / mid / high colors for metabolite values."
            )
else:

    class AppearancePanel:
        def __init__(self, *args, **kwargs):
            raise ImportError(
                'PySide6 is required for GUI. Install with: pip install "pathview-plus[gui]"'
            )
