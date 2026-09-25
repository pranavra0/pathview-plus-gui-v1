"""Offline-first organism and pathway catalog operations."""

from __future__ import annotations

import re
from pathlib import Path

from pathview import SBGN_SOURCES, get_species_code, list_sbgn_pathways, search_organisms

KEGG_ID = re.compile(r"^(?:[A-Za-z][A-Za-z0-9_]*\s*)?\d{5}$")


def species_search(query: str, limit: int = 30):
    return search_organisms(query, limit=limit)


def identify(pathway_id: str) -> str:
    from pathview.databases import detect_database

    return detect_database(pathway_id)


def resolve_species(value: str):
    return get_species_code(value)


def sbgn_sources() -> dict[str, str]:
    return {"": "All", **SBGN_SOURCES}


def search_sbgn(source: str | None = None, query: str | None = None, limit: int = 100):
    return list_sbgn_pathways(
        source=source or None, query=query or None, limit=min(limit, 100)
    )


def parse_kegg_ids(text: str) -> list[str]:
    """Normalize separators and retain ordered unique syntactically valid IDs."""
    values = re.split(r"[\s,]+", text.strip()) if text.strip() else []
    result: list[str] = []
    for value in values:
        if not value:
            continue
        if not KEGG_ID.fullmatch(value):
            raise ValueError(f"Invalid KEGG pathway identifier: {value}")
        numeric = re.search(r"\d{5}$", value).group(0)
        if numeric not in result:
            result.append(numeric)
    return result


def add_local_sbgn(path: str | Path) -> Path:
    local = Path(path)
    if local.suffix.lower() != ".sbgn":
        raise ValueError("SBGN pathway files must use the .sbgn extension.")
    if not local.is_file():
        raise FileNotFoundError(local)
    return local


__all__ = [
    "KEGG_ID",
    "species_search",
    "resolve_species",
    "sbgn_sources",
    "search_sbgn",
    "parse_kegg_ids",
    "add_local_sbgn",
]
