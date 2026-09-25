from __future__ import annotations


def test_pathway_selector_collects_ordered_ids(qapp):
    from pathview.gui.widgets.pathway_selector import PathwaySelector

    selector = PathwaySelector()
    selector.ids.setText("04110, 04010, 00020")

    assert selector.values() == ["04110", "04010", "00020"]
    assert selector.database.currentText() == "kegg"
