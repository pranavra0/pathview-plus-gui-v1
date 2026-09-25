"""Typed, Qt-free application state and render configuration models."""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Literal


@dataclass
class DataConfig:
    path: Path | None = None
    id_type: str = "ENTREZ"
    enabled: bool = False

    @property
    def filename(self) -> str | None:
        return str(self.path) if self.path else None


@dataclass
class ColorScaleConfig:
    palette: str = "rdbu"
    limit: float = 1.0
    bins: int = 10
    both_dirs: bool = True
    discrete: bool = False


@dataclass(init=False)
class RenderConfig:
    """Immutable-at-render-boundary configuration (the GUI copies it)."""

    mode: Literal["kegg", "sbgn"] = "kegg"
    pathways: list[str | Path] = field(default_factory=list)
    gene: DataConfig = field(default_factory=lambda: DataConfig(id_type="ENTREZ"))
    compound: DataConfig = field(default_factory=lambda: DataConfig(id_type="KEGG"))
    species: str = "hsa"
    output_dir: Path = field(default_factory=lambda: Path("."))
    output_format: str = "png"
    theme: str = "publication"
    title: str | None = None
    subtitle: str | None = None
    figure_width: float = 14.0
    dpi: int = 220
    gene_scale: ColorScaleConfig | None = field(default_factory=ColorScaleConfig)
    compound_scale: ColorScaleConfig | None = field(
        default_factory=lambda: ColorScaleConfig(palette="viridis")
    )
    map_without_data: bool = False
    offline: bool = False
    source: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    def __init__(
        self,
        mode: Literal["kegg", "sbgn"] = "kegg",
        pathways: list[str | Path] | None = None,
        gene: DataConfig | None = None,
        compound: DataConfig | None = None,
        species: str = "hsa",
        output_dir: Path | str = Path("."),
        output_format: str = "png",
        theme: str = "publication",
        title: str | None = None,
        subtitle: str | None = None,
        figure_width: float = 14.0,
        dpi: int = 220,
        gene_scale: ColorScaleConfig | None = None,
        compound_scale: ColorScaleConfig | None = None,
        map_without_data: bool = False,
        offline: bool = False,
        source: str | None = None,
        extra: dict[str, Any] | None = None,
        *,
        pathway_ids: list[str] | None = None,
        database: str | None = None,
        gene_file: str | None = None,
        cpd_file: str | None = None,
        gene_idtype: str | None = None,
        cpd_idtype: str | None = None,
        render_mode: str | None = None,
    ):
        self.mode = database or mode
        self.pathways = list(pathways if pathways is not None else (pathway_ids or []))
        if isinstance(gene, dict):
            gene = DataConfig(
                Path(gene["path"]) if gene.get("path") else None,
                gene.get("id_type", "ENTREZ"),
                bool(gene.get("enabled", False)),
            )
        if isinstance(compound, dict):
            compound = DataConfig(
                Path(compound["path"]) if compound.get("path") else None,
                compound.get("id_type", "KEGG"),
                bool(compound.get("enabled", False)),
            )
        self.gene = gene or DataConfig(
            id_type=gene_idtype or ("SYMBOL" if self.mode == "sbgn" else "ENTREZ")
        )
        self.compound = compound or DataConfig(id_type=cpd_idtype or "KEGG")
        if gene_file is not None:
            self.gene = DataConfig(Path(gene_file), gene_idtype or self.gene.id_type, True)
        if cpd_file is not None:
            self.compound = DataConfig(
                Path(cpd_file), cpd_idtype or self.compound.id_type, True
            )
        if gene_idtype is not None:
            self.gene.id_type = gene_idtype
        if cpd_idtype is not None:
            self.compound.id_type = cpd_idtype
        self.species = species
        self.output_dir = Path(output_dir)
        self.output_format = output_format
        self.theme = theme
        self.title = title
        self.subtitle = subtitle
        self.figure_width = figure_width
        self.dpi = dpi
        self.gene_scale = gene_scale if gene_scale is not None else ColorScaleConfig()
        self.compound_scale = (
            compound_scale
            if compound_scale is not None
            else ColorScaleConfig(palette="viridis")
        )
        self.map_without_data = map_without_data
        self.offline = offline
        self.source = source
        self.extra = dict(extra or {})
        if render_mode is not None:
            self.extra["render_mode"] = render_mode

    # Compatibility conveniences used by simple clients and older tests.
    @property
    def pathway_ids(self) -> list[str]:
        return [str(p) for p in self.pathways]

    @pathway_ids.setter
    def pathway_ids(self, values: list[str]) -> None:
        self.pathways = list(values)

    @property
    def database(self) -> str:
        return self.mode

    @database.setter
    def database(self, value: str) -> None:
        self.mode = value  # type: ignore[assignment]

    @property
    def gene_file(self) -> str | None:
        return self.gene.filename

    @gene_file.setter
    def gene_file(self, value: str | None) -> None:
        self.gene.path = Path(value) if value else None
        self.gene.enabled = bool(value)

    @property
    def cpd_file(self) -> str | None:
        return self.compound.filename

    @cpd_file.setter
    def cpd_file(self, value: str | None) -> None:
        self.compound.path = Path(value) if value else None
        self.compound.enabled = bool(value)

    @property
    def render_mode(self) -> str:
        return str(self.extra.get("render_mode", "auto"))

    @render_mode.setter
    def render_mode(self, value: str) -> None:
        self.extra["render_mode"] = value

    def copy(self) -> RenderConfig:
        return RenderConfig.from_dict(self.to_dict())

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["pathways"] = [str(p) for p in self.pathways]
        data["output_dir"] = str(self.output_dir)
        for key in ("gene", "compound"):
            data[key]["path"] = str(data[key]["path"]) if data[key]["path"] else None
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RenderConfig:
        raw = dict(data)
        # Accept the compact example schema and the in-memory schema.
        if "database" in raw and "mode" not in raw:
            raw["mode"] = raw.pop("database")
        if "pathway_ids" in raw and "pathways" not in raw:
            raw["pathways"] = raw.pop("pathway_ids")
        for key, default_type in (("gene", "ENTREZ"), ("compound", "KEGG")):
            if key not in raw:
                legacy = "gene_file" if key == "gene" else "cpd_file"
                raw[key] = {
                    "path": raw.pop(legacy, None),
                    "id_type": default_type,
                    "enabled": bool(raw.get(legacy)),
                }
            elif isinstance(raw[key], dict):
                raw[key] = DataConfig(
                    path=Path(raw[key]["path"]) if raw[key].get("path") else None,
                    id_type=raw[key].get("id_type", default_type),
                    enabled=bool(raw[key].get("enabled", False)),
                )
        if "output_dir" in raw:
            raw["output_dir"] = Path(raw["output_dir"])
        for key in ("gene_scale", "compound_scale"):
            if isinstance(raw.get(key), dict):
                fields = {
                    field.name for field in ColorScaleConfig.__dataclass_fields__.values()
                }
                raw[key] = ColorScaleConfig(
                    **{k: v for k, v in raw[key].items() if k in fields}
                )
        allowed = {f.name for f in cls.__dataclass_fields__.values()}
        return cls(**{k: v for k, v in raw.items() if k in allowed})


@dataclass(init=False)
class RunResult:
    pathway: str
    source: str = "KEGG"
    status: str = "Queued"
    result: Any = None
    output_path: Path | None = None
    error: str | None = None
    warnings: list[str] = field(default_factory=list)

    def __init__(
        self,
        pathway: str,
        output_path: str | Path | None = None,
        status: str = "Queued",
        source: str = "KEGG",
        result: Any = None,
        error: str | None = None,
        warnings: list[str] | None = None,
    ):
        self.pathway = str(pathway)
        self.source = source
        self.status = status
        self.result = result
        self.output_path = Path(output_path) if output_path else None
        self.error = error
        self.warnings = list(warnings or [])

    @property
    def pathway_id(self) -> str:
        return self.pathway

    @property
    def message(self) -> str:
        return self.error or ""

    @property
    def diagnostics(self) -> dict[str, Any]:
        return getattr(self.result, "diagnostics", {}) if self.result else {}


@dataclass(init=False)
class AppState:
    project_path: Path | None = None
    kegg_config: RenderConfig = field(default_factory=RenderConfig)
    sbgn_config: RenderConfig = field(
        default_factory=lambda: RenderConfig(mode="sbgn", gene=DataConfig(id_type="SYMBOL"))
    )
    current_mode: Literal["kegg", "sbgn"] = "kegg"
    current_results: list[RunResult] = field(default_factory=list)
    dirty: bool = False
    offline: bool = False
    log: list[str] = field(default_factory=list)

    def __init__(
        self,
        project_path: Path | None = None,
        kegg_config: RenderConfig | None = None,
        sbgn_config: RenderConfig | None = None,
        current_mode: Literal["kegg", "sbgn"] = "kegg",
        current_results: list[RunResult] | None = None,
        dirty: bool = False,
        offline: bool = False,
        log: list[str] | None = None,
        config: RenderConfig | None = None,
        results: list[RunResult] | None = None,
    ):
        if config is not None:
            if config.mode == "sbgn":
                sbgn_config = config
            else:
                kegg_config = config
            current_mode = config.mode
        self.project_path = project_path
        self.kegg_config = kegg_config or RenderConfig()
        self.sbgn_config = sbgn_config or RenderConfig(
            mode="sbgn", gene=DataConfig(id_type="SYMBOL")
        )
        self.current_mode = current_mode
        self.current_results = list(
            current_results if current_results is not None else (results or [])
        )
        self.dirty = dirty
        self.offline = offline
        self.log = list(log or [])

    @property
    def results(self) -> list[RunResult]:
        return self.current_results

    @results.setter
    def results(self, value: list[RunResult]) -> None:
        self.current_results = value

    @property
    def config(self) -> RenderConfig:
        return self.kegg_config if self.current_mode == "kegg" else self.sbgn_config

    def snapshot(self) -> RenderConfig:
        config = self.config.copy()
        config.offline = self.offline
        return config

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "mode": self.current_mode,
            "gene": {
                "enabled": self.config.gene.enabled,
                "path": self.config.gene.filename,
                "id_type": self.config.gene.id_type,
            },
            "compound": {
                "enabled": self.config.compound.enabled,
                "path": self.config.compound.filename,
                "id_type": self.config.compound.id_type,
            },
            "species": self.config.species,
            "pathways": [str(p) for p in self.config.pathways],
            "appearance": {
                "theme": self.config.theme,
                "output_format": self.config.output_format,
                "dpi": self.config.dpi,
                "figure_width": self.config.figure_width,
                "title": self.config.title,
                "subtitle": self.config.subtitle,
            },
            "output_dir": str(self.config.output_dir),
            "extra": self.config.extra,
            "offline": self.offline,
            "config": self.config.to_dict(),
            "results": [
                {
                    "pathway": r.pathway,
                    "source": r.source,
                    "status": r.status,
                    "output_path": str(r.output_path) if r.output_path else None,
                    "error": r.error,
                    "warnings": r.warnings,
                }
                for r in self.current_results
            ],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AppState:
        if "config" in data:
            config = RenderConfig.from_dict(data["config"])
        else:
            mode = str(data.get("mode", "kegg"))
            gene = data.get("gene", {})
            compound = data.get("compound", {})
            appearance = data.get("appearance", {})
            config = RenderConfig(
                mode=mode if mode in ("kegg", "sbgn") else "kegg",
                pathways=list(data.get("pathways", [])),
                gene=DataConfig(
                    Path(gene["path"]) if gene.get("path") else None,
                    gene.get("id_type", "ENTREZ"),
                    bool(gene.get("enabled", False)),
                ),
                compound=DataConfig(
                    Path(compound["path"]) if compound.get("path") else None,
                    compound.get("id_type", "KEGG"),
                    bool(compound.get("enabled", False)),
                ),
                species=str(data.get("species", "hsa")),
                output_dir=Path(data.get("output_dir", ".")),
                output_format=str(appearance.get("output_format", "png")),
                theme=str(appearance.get("theme", "publication")),
                dpi=int(appearance.get("dpi", 220)),
                figure_width=float(appearance.get("figure_width", 14.0)),
                title=appearance.get("title"),
                subtitle=appearance.get("subtitle"),
                extra=dict(data.get("extra", {})),
            )
        state = cls(
            config=config,
            current_mode=config.mode,
            offline=bool(data.get("offline", False)),
        )
        state.current_results = [
            RunResult(
                r.get("pathway", r.get("pathway_id", "")),
                r.get("output_path"),
                r.get("status", "Queued"),
                r.get("source", config.mode.upper()),
                error=r.get("error"),
                warnings=r.get("warnings", []),
            )
            for r in data.get("results", [])
        ]
        return state


def validate_config(config: RenderConfig) -> list[str]:
    errors: list[str] = []
    if not config.pathways:
        errors.append("Select at least one pathway.")
    if config.mode not in {"kegg", "sbgn"}:
        errors.append("Pathway mode must be KEGG or SBGN.")
    if config.mode == "kegg" and not config.species.strip():
        errors.append("Species is required for KEGG pathways.")
    if (
        not any(d.enabled and d.path for d in (config.gene, config.compound))
        and not config.map_without_data
    ):
        errors.append("Enable gene or compound data, or select map-only rendering.")
    if config.output_format not in {"png", "svg", "pdf"}:
        errors.append("Output format must be PNG, SVG, or PDF.")
    if not config.output_dir.exists():
        try:
            config.output_dir.mkdir(parents=True, exist_ok=True)
        except OSError:
            errors.append("Cannot write to output directory.")
    elif not config.output_dir.is_dir():
        errors.append("Cannot write to output directory.")
    if config.dpi < 72 or config.dpi > 600:
        errors.append("DPI must be between 72 and 600.")
    if config.figure_width <= 0 or not math.isfinite(config.figure_width):
        errors.append("Figure width must be a positive finite number.")
    for label, data in (("Gene", config.gene), ("Compound", config.compound)):
        if data.enabled and (not data.path or not data.path.is_file()):
            errors.append(f"{label} data file does not exist: {data.path or '(none)'}")
    for label, scale in (("Gene", config.gene_scale), ("Compound", config.compound_scale)):
        if scale and (scale.limit <= 0 or not math.isfinite(scale.limit) or scale.bins < 1):
            errors.append(
                f"{label} colour scale limit must be positive and bins must be at least 1."
            )
    if (
        config.extra.get("node_sum") == "random"
        and config.extra.get("rand_seed") is not None
    ):
        try:
            int(config.extra["rand_seed"])
        except (TypeError, ValueError):
            errors.append("Random seed must be an integer.")
    return errors
