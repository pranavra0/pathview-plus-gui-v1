from __future__ import annotations

import json

from pathview.gui.models import AppState, RenderConfig, RunResult
from pathview.gui.services.project_service import load_project, save_project


def test_project_save_load_round_trip_preserves_configuration(tmp_path):
    state = AppState(
        config=RenderConfig(
            pathway_ids=["04110", "04010"],
            database="kegg",
            species="hsa",
            gene_file="data/rna.tsv",
            output_format="svg",
            render_mode="vector",
            extra={"map_null": False},
        ),
        results=[RunResult("04110", "/tmp/hsa04110.pathview.svg", "success")],
        offline=True,
    )
    project = tmp_path / "analysis.pvp.json"

    save_project(state, project)
    loaded = load_project(project)

    assert loaded.config.pathway_ids == ["04110", "04010"]
    assert loaded.config.gene_file == "data/rna.tsv"
    assert loaded.config.output_format == "svg"
    assert loaded.results[0].status == "success"
    assert loaded.offline is True


def test_project_loader_ignores_future_unknown_fields(tmp_path):
    project = tmp_path / "future.pvp.json"
    project.write_text(
        json.dumps(
            {
                "schema_version": 99,
                "config": {"pathway_ids": ["00020"], "future_option": "ignored"},
                "future_section": {"new_widget": True},
            }
        )
    )

    loaded = load_project(project)

    assert loaded.config.pathway_ids == ["00020"]
    assert not hasattr(loaded.config, "future_option")
