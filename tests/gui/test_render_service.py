from __future__ import annotations

from pathlib import Path

from pathview.gui.models import RenderConfig
from pathview.gui.services.render_service import render


def test_offline_vector_render_uses_fixture_and_returns_output(tmp_path, fixtures_dir):
    config = RenderConfig(
        pathway_ids=["00020"],
        species="hsa",
        output_dir=str(tmp_path),
        output_format="png",
        render_mode="vector",
        offline=True,
        extra={"kegg_dir": str(fixtures_dir), "map_null": True},
    )

    results = render(config)

    assert len(results) == 1
    assert results[0].status == "success"
    assert results[0].output_path is not None
    assert Path(results[0].output_path).exists()
    assert isinstance(results[0].diagnostics, dict)


def test_batch_continues_after_a_failed_pathway(monkeypatch, tmp_path):
    import pathview

    class FakeResult:
        output_path = tmp_path / "ok.png"
        diagnostics = {"nodes": 2}

    def fake_pathview(pathway, **kwargs):
        if pathway == "bad":
            raise RuntimeError("bad pathway")
        FakeResult.output_path.touch()
        return FakeResult()

    monkeypatch.setattr(pathview, "pathview", fake_pathview)
    config = RenderConfig(pathway_ids=["good", "bad", "later"], output_dir=str(tmp_path))

    results = render(config)

    assert [r.pathway_id for r in results] == ["good", "bad", "later"]
    assert results[0].status == "success"
    assert results[1].status == "error"
    assert results[2].status == "success"
