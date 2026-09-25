"""Reusable molecular table input parsing."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import polars as pl


@dataclass
class TableLoadResult:
    """Parsed molecular table and information about discarded columns."""

    data: pl.DataFrame
    ignored_columns: list[str]
    id_column: str
    value_columns: list[str]


def read_molecular_table(path: str | Path) -> TableLoadResult:
    """Read a CSV/TSV-like molecular table using the CLI's semantics.

    The first column is the identifier column. Remaining columns are coerced
    to floating point; columns containing no numeric values are ignored.
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(p)

    sep = {".tsv": "\t", ".txt": "\t", ".tab": "\t"}.get(p.suffix.lower(), ",")
    try:
        df = pl.read_csv(p, separator=sep, infer_schema_length=0)
        # A few spreadsheet exports carry tab-separated content with a .csv
        # suffix. Recover that unambiguously when comma parsing yields one
        # column; ordinary one-column files remain rejected below.
        if df.width < 2 and sep == ",":
            first_line = p.read_text(encoding="utf-8", errors="replace").splitlines()[0]
            if "\t" in first_line:
                df = pl.read_csv(p, separator="\t", infer_schema_length=0)
    except Exception as exc:
        raise ValueError(str(exc)) from exc

    if df.width < 2:
        raise ValueError(
            f"{df.width} column(s); an identifier column plus at least one value column is required."
        )
    id_col = df.columns[0]
    value_cols = df.columns[1:]
    df = df.with_columns(
        [pl.col(id_col).cast(pl.String)]
        + [pl.col(c).cast(pl.Float64, strict=False) for c in value_cols]
    )
    usable = [c for c in value_cols if df[c].null_count() < df.height]
    ignored = [c for c in value_cols if c not in usable]
    if not usable:
        raise ValueError(
            f"no numeric value column in {p.name}. Columns after the first must be numeric; found {value_cols}."
        )
    return TableLoadResult(
        data=df.select([id_col] + usable),
        ignored_columns=ignored,
        id_column=id_col,
        value_columns=usable,
    )
