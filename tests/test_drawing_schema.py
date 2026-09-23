from pyflowsheet.schema import (
    DrawingFrameSettingsSchema,
    FlowsheetSchema,
    MetadataSchema,
)


def test_metadata_schema_drafting_fields():
    meta = MetadataSchema(
        id="WT_01",
        name="Water Treatment",
        title="WATER TREATMENT SYSTEM",
        subtitle="PROCESS FLOW DIAGRAM",
        drawing_number="DWG-001",
        revision="B",
        sheet_size="D",
        scale="NTS",
        sheet="1 OF 1",
        cage_code="1A2B3",
        contract_no="ENG-2026",
        projection="THIRD ANGLE",
        code_standard="ANSI/ASME Y14.1 / ISA-5.1",
    )
    assert meta.cage_code == "1A2B3"
    assert meta.contract_no == "ENG-2026"
    assert meta.projection == "THIRD ANGLE"
    assert meta.code_standard == "ANSI/ASME Y14.1 / ISA-5.1"


def test_drawing_frame_settings_schema():
    cfg = DrawingFrameSettingsSchema(
        enabled=True,
        sheet_size="D",
        show_border=True,
        show_title_block=True,
        show_revision_block=True,
        show_legend=True,
        show_notes=True,
    )
    assert cfg.enabled is True
    assert cfg.sheet_size == "D"


def test_drawing_frame_settings_schema_defaults():
    cfg = DrawingFrameSettingsSchema()
    assert cfg.enabled is True
    assert cfg.sheet_size == "D"
    assert cfg.show_border is True
    assert cfg.show_title_block is True
    assert cfg.show_revision_block is True
    assert cfg.show_legend is True
    assert cfg.show_notes is True
    assert cfg.custom_legend_entries == []


def test_flowsheet_schema_with_frame_settings():
    raw = {
        "schema_version": "1.0",
        "metadata": {
            "id": "TEST",
            "drawing_number": "DWG-100",
            "cage_code": "99999",
        },
        "settings": {
            "drawing_frame": {
                "enabled": True,
                "sheet_size": "D",
            }
        },
    }
    schema = FlowsheetSchema.model_validate(raw)
    assert schema.metadata.cage_code == "99999"
    assert schema.settings["drawing_frame"]["sheet_size"] == "D"
