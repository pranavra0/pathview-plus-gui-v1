from __future__ import annotations

from pathview.gui.models import RenderConfig, validate_config


def test_validation_requires_pathway_and_valid_output_format():
    errors = validate_config(RenderConfig(output_format="jpeg"))

    assert any("pathway" in error.lower() for error in errors)
    assert any("output format" in error.lower() for error in errors)


def test_validation_accepts_existing_inputs_and_sbgn_without_species(tmp_path):
    gene = tmp_path / "genes.csv"
    gene.write_text("id,value\nA,1\n")
    config = RenderConfig(
        pathway_ids=["P00001"],
        database="sbgn",
        species="",
        gene_file=str(gene),
    )

    assert validate_config(config) == []


def test_validation_reports_missing_input_file(tmp_path):
    config = RenderConfig(pathway_ids=["04110"], gene_file=str(tmp_path / "gone.tsv"))

    errors = validate_config(config)

    assert len(errors) == 1
    assert "Gene data file does not exist" in errors[0]
