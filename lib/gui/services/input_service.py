"""Molecular file loading for presentation-independent GUI services."""

from __future__ import annotations

from pathlib import Path

import polars as pl
from pathview.input_io import TableLoadResult, read_molecular_table


def read_table(path: str | Path) -> pl.DataFrame:
    """Load a molecular table using exactly the CLI parsing semantics."""
    return read_molecular_table(path).data


def inspect_table(path: str | Path, limit: int = 50) -> dict:
    """Return bounded preview metadata without copying the full table."""
    result = read_molecular_table(path)
    source = Path(path)
    separator = "\t" if source.suffix.lower() in {".tsv", ".tab", ".txt"} else ","
    try:
        columns = pl.read_csv(source, separator=separator, infer_schema_length=0).columns
    except Exception:
        columns = [result.id_column, *result.value_columns, *result.ignored_columns]
    return {
        "path": str(path),
        "rows": result.data.height,
        "columns": columns,
        "id_column": result.id_column,
        "numeric_columns": result.value_columns,
        "ignored_columns": result.ignored_columns,
        "conditions": len(result.value_columns),
        "preview": result.data.head(max(0, min(int(limit), 50))),
    }


def load_optional(path: str | Path | None) -> pl.DataFrame | None:
    return read_table(path) if path else None


__all__ = ["TableLoadResult", "read_table", "inspect_table", "load_optional"]
