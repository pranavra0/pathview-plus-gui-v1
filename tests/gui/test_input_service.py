from __future__ import annotations

import polars as pl
import pytest
from pathview.gui.services.input_service import inspect_table, read_table
from pathview.input_io import read_molecular_table


def test_csv_preview_reports_rows_columns_and_numeric_values(tmp_path):
    source = tmp_path / "rna.csv"
    source.write_text("entrez,Control,Treated,note\nTP53,1.5,2.0,ok\nEGFR,-1,0.5,ok\n")

    preview = inspect_table(source, limit=1)

    assert preview["rows"] == 2
    assert preview["columns"] == ["entrez", "Control", "Treated", "note"]
    assert preview["numeric_columns"] == ["Control", "Treated"]
    assert preview["preview"].height == 1


def test_tabular_extensions_are_read_as_tsv(tmp_path):
    source = tmp_path / "metabolites.tab"
    source.write_text("kegg\tlog2fc\nC00031\t1.25\n")

    table = read_table(source)

    assert table.shape == (1, 2)
    assert table.columns == ["kegg", "log2fc"]
    assert table["kegg"].to_list() == ["C00031"]


def test_shared_loader_preserves_ids_and_reports_ignored_columns(tmp_path):
    source = tmp_path / "mixed.tsv"
    source.write_text("id\tvalue\tdescription\n001\t2.0\tcase\n002\t-1.0\tcontrol\n")

    result = read_molecular_table(source)

    assert result.data["id"].dtype == pl.String
    assert result.value_columns == ["value"]
    assert result.ignored_columns == ["description"]


def test_shared_loader_rejects_file_without_numeric_measurements(tmp_path):
    source = tmp_path / "bad.csv"
    source.write_text("id\tdescription\nA\ttext\n")

    with pytest.raises(ValueError, match="numeric value column"):
        read_molecular_table(source)
