"""Qt-free adapter from GUI configuration to Pathview+ public APIs."""

from __future__ import annotations

import warnings
from collections.abc import Callable
from pathlib import Path

from ..models import RenderConfig, RunResult
from .input_service import load_optional


class RenderService:
    """Render one pathway at a time; the caller owns batching and threading."""

    def render_one(self, config: RenderConfig, pathway: str | Path) -> RunResult:
        from pathview.cache import set_offline

        from pathview import pathview, sbgnview

        set_offline(config.offline)
        gene = (
            load_optional(config.gene.path)
            if config.gene.enabled and config.gene.path
            else None
        )
        compound = (
            load_optional(config.compound.path)
            if config.compound.enabled and config.compound.path
            else None
        )
        Path(config.output_dir).mkdir(parents=True, exist_ok=True)
        kwargs = {
            "gene_data": gene,
            "cpd_data": compound,
            "out_dir": config.output_dir,
            "output_format": config.output_format,
            "theme": config.theme,
            "title": config.title,
            "subtitle": config.subtitle,
            "figure_width": config.figure_width,
            "dpi": config.dpi,
            "quiet": True,
            "continue_on_error": False,
            "gene_idtype": config.gene.id_type,
            "cpd_idtype": config.compound.id_type,
            "limit": {
                "gene": config.gene_scale.limit if config.gene_scale else 1.0,
                "cpd": config.compound_scale.limit if config.compound_scale else 1.0,
            },
            "bins": config.gene_scale.bins if config.gene_scale else 10,
            "gene_color": config.gene_scale.palette if config.gene_scale else None,
            "cpd_color": config.compound_scale.palette if config.compound_scale else None,
            "plot_col_key": bool(config.extra.get("plot_col_key", True)),
            "node_sum": config.extra.get("node_sum", "sum"),
            "rand_seed": int(config.extra["rand_seed"])
            if config.extra.get("rand_seed") is not None
            else None,
            "map_cpd_name": bool(config.extra.get("map_cpd_name", True)),
        }
        if config.mode == "kegg":
            kwargs.update(
                species=config.species,
                kegg_dir=config.extra.get("kegg_dir", "."),
                render_mode=config.extra.get("render_mode", "auto"),
                draw_edges=bool(config.extra.get("draw_edges", True)),
                show_link_edges=bool(config.extra.get("show_link_edges", False)),
                both_dirs={
                    "gene": config.gene_scale.both_dirs if config.gene_scale else True,
                    "cpd": config.compound_scale.both_dirs
                    if config.compound_scale
                    else True,
                },
                discrete={
                    "gene": config.gene_scale.discrete if config.gene_scale else False,
                    "cpd": config.compound_scale.discrete
                    if config.compound_scale
                    else False,
                },
                map_null=config.map_without_data
                or bool(config.extra.get("map_null", False)),
                min_nnodes=int(config.extra.get("min_nnodes", 3)),
                split_group=bool(config.extra.get("split_group", False)),
                expand_node=bool(config.extra.get("expand_node", False)),
                map_symbol=bool(config.extra.get("map_symbol", True)),
            )
            function = pathview
            source = "KEGG"
        else:
            kwargs.update(
                sbgn_dir=config.extra.get("sbgn_dir", "."),
                show_compartments=bool(config.extra.get("show_compartments", True)),
                show_processes=bool(config.extra.get("show_processes", True)),
                draw_edges=bool(config.extra.get("draw_edges", True)),
                overwrite=bool(config.extra.get("overwrite", False)),
            )
            function = sbgnview
            source = config.source or "SBGN"

        captured: list[str] = []
        with warnings.catch_warnings(record=True) as warning_list:
            warnings.simplefilter("always")
            result = function(pathway, **kwargs)
            captured.extend(str(item.message) for item in warning_list)
        return RunResult(
            pathway=str(pathway),
            source=source,
            status="success",
            result=result,
            output_path=getattr(result, "output_path", None),
            warnings=captured,
        )

    def render_batch(
        self,
        config: RenderConfig,
        cancel: Callable[[], bool] | None = None,
        on_started: Callable[[int, int, str], None] | None = None,
    ) -> list[RunResult]:
        results: list[RunResult] = []
        pathways = list(config.pathways)
        for index, pathway in enumerate(pathways):
            if cancel and cancel():
                results.extend(
                    RunResult(str(p), status="cancelled") for p in pathways[index:]
                )
                break
            if on_started:
                on_started(index, len(pathways), str(pathway))
            try:
                results.append(self.render_one(config, pathway))
            except Exception as exc:
                results.append(
                    RunResult(
                        pathway=str(pathway),
                        source="KEGG" if config.mode == "kegg" else "SBGN",
                        status="error",
                        error=f"{type(exc).__name__}: {exc}",
                    )
                )
        return results


def render(
    config: RenderConfig, cancel: Callable[[], bool] | None = None
) -> list[RunResult]:
    """Compatibility function used by the worker and service-level clients."""
    return RenderService().render_batch(config, cancel=cancel)


__all__ = ["RenderService", "render"]
